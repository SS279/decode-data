# Memory Optimization for Render Free Tier (512MB)

## Problem
On November 25, 2025, encountered OOM (Out of Memory) errors during dbt seed operations:
```
[2025-11-25 10:16:36 +0000] [55] [ERROR] Worker (pid:86) was sent SIGKILL! Perhaps out of memory?
```

## Root Cause
The application is deployed on Render's free tier with only **512MB RAM**. The OOM error was caused by:
1. Multiple Gunicorn workers (2-4 by default) consuming 200-600MB
2. MotherDuck connection pool allowing up to 5 concurrent connections
3. Up to 3 concurrent dbt jobs allowed
4. Up to 5 concurrent requests per user

Total memory usage could easily exceed 512MB during normal operations.

## Changes Made (November 25, 2025)

### 1. Gunicorn Worker Limit
**File**: `render.yaml` (new file)
- **Change**: Set `WEB_CONCURRENCY=1` to limit Gunicorn to a single worker
- **Impact**: Reduces base memory usage from 200-600MB to 50-120MB
- **Trade-off**: Reduced concurrency, but acceptable for free tier

### 2. MotherDuck Connection Pool
**File**: `learning/storage.py:107`
- **Before**: `max_connections=5`
- **After**: `max_connections=2`
- **Impact**: Reduces connection pool memory from 100-250MB to 40-100MB
- **Trade-off**: Fewer concurrent database operations, but prevents OOM

### 3. Concurrent dbt Jobs
**File**: `learning/dbt_manager.py:22`
- **Before**: `MAX_CONCURRENT_JOBS = 3`
- **After**: `MAX_CONCURRENT_JOBS = 1`
- **Impact**: Prevents multiple dbt operations running simultaneously
- **Trade-off**: Jobs queue sequentially, but ensures reliability

### 4. Concurrent User Requests
**File**: `learning/middleware.py:141`
- **Before**: `MAX_CONCURRENT_REQUESTS = 5`
- **After**: `MAX_CONCURRENT_REQUESTS = 3`
- **Impact**: Limits simultaneous operations per user
- **Trade-off**: Slight reduction in responsiveness under heavy load

## Expected Results
- **Memory Usage**: Reduced from 600-800MB peak to 200-400MB peak
- **OOM Errors**: Should be eliminated for typical usage patterns
- **Performance**: Slightly slower under heavy concurrent load, but more stable

## Deployment Notes
The `render.yaml` file provides infrastructure-as-code configuration. However, if you're using the Render dashboard:
1. Go to your service settings in Render dashboard
2. Add environment variable: `WEB_CONCURRENCY=1`
3. Redeploy the service

## Monitoring
Watch for these indicators:
- **OOM still occurring**: Consider upgrading to Render's paid tier (512MB → 2GB+)
- **Slow response times**: May need to increase concurrent request limits
- **Queue buildup**: May need to increase MAX_CONCURRENT_JOBS (but watch memory)

## Future Optimizations
If upgrading to a paid tier with more memory:
1. Increase `WEB_CONCURRENCY` to 2-4 workers
2. Increase `max_connections` to 5-10
3. Increase `MAX_CONCURRENT_JOBS` to 2-3
4. Increase `MAX_CONCURRENT_REQUESTS` to 5-10

## Related Files
- Previous optimizations: `OPTIMIZATION_SUMMARY.md` (Nov 24, 2025)
- Configuration: `render.yaml`, `learning/storage.py`, `learning/dbt_manager.py`, `learning/middleware.py`
