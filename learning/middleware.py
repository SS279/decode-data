"""
Custom middleware for rate limiting and request throttling
"""
import time
import threading
from django.http import JsonResponse
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class SimpleRateLimitMiddleware:
    """
    Simple in-memory rate limiting middleware to prevent resource exhaustion.

    Limits:
    - 100 requests per minute per IP
    - 20 requests per minute for expensive operations (dbt, AI)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # In-memory storage for rate limits (IP -> (count, timestamp))
        self._rate_limits = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def __call__(self, request):
        # Get client IP
        ip = self._get_client_ip(request)

        # Determine rate limit based on path
        limit, window = self._get_rate_limit(request.path)

        # Check rate limit
        if not self._check_rate_limit(ip, limit, window):
            logger.warning(f"Rate limit exceeded for IP: {ip} on path: {request.path}")
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.'
            }, status=429)

        # Cleanup old entries periodically (every 5 minutes)
        if time.time() - self._last_cleanup > 300:
            self._cleanup_old_entries()

        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

    def _get_rate_limit(self, path):
        """
        Determine rate limit based on request path.
        Returns: (requests_per_window, window_seconds)
        """
        # Expensive operations - stricter limits
        expensive_paths = [
            '/lesson/',  # Model builder and execution
            '/api/ai/',  # AI operations
            '/api/stream-logs/',  # Streaming endpoints
        ]

        for expensive_path in expensive_paths:
            if expensive_path in path:
                return 20, 60  # 20 requests per minute

        # Default rate limit for all other requests
        return 100, 60  # 100 requests per minute

    def _check_rate_limit(self, ip, limit, window):
        """Check if request is within rate limit"""
        with self._lock:
            current_time = time.time()
            key = f"{ip}"

            if key not in self._rate_limits:
                # First request from this IP
                self._rate_limits[key] = {
                    'count': 1,
                    'window_start': current_time
                }
                return True

            rate_data = self._rate_limits[key]
            window_elapsed = current_time - rate_data['window_start']

            if window_elapsed > window:
                # Window expired, reset counter
                self._rate_limits[key] = {
                    'count': 1,
                    'window_start': current_time
                }
                return True

            # Within window
            if rate_data['count'] < limit:
                # Under limit, increment and allow
                rate_data['count'] += 1
                return True
            else:
                # Over limit, deny
                return False

    def _cleanup_old_entries(self):
        """Remove rate limit entries older than 5 minutes"""
        with self._lock:
            current_time = time.time()
            keys_to_delete = []

            for key, data in self._rate_limits.items():
                if current_time - data['window_start'] > 300:  # 5 minutes
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._rate_limits[key]

            if keys_to_delete:
                logger.info(f"Cleaned up {len(keys_to_delete)} old rate limit entries")

            self._last_cleanup = current_time


class ConcurrentRequestLimitMiddleware:
    """
    Limit concurrent requests per user to prevent resource exhaustion.
    Maximum 5 concurrent requests per authenticated user.
    """

    # Class-level storage for active requests per user
    _active_requests = {}
    _lock = threading.Lock()
    MAX_CONCURRENT_REQUESTS = 5

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        user_id = str(request.user.id)

        # Check and increment active requests
        with self._lock:
            current_count = self._active_requests.get(user_id, 0)
            if current_count >= self.MAX_CONCURRENT_REQUESTS:
                logger.warning(f"Concurrent request limit exceeded for user: {user_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Too many concurrent requests. Please wait for previous requests to complete.'
                }, status=429)

            self._active_requests[user_id] = current_count + 1

        try:
            # Process request
            response = self.get_response(request)
            return response
        finally:
            # Decrement active requests
            with self._lock:
                if user_id in self._active_requests:
                    self._active_requests[user_id] -= 1
                    if self._active_requests[user_id] <= 0:
                        del self._active_requests[user_id]
