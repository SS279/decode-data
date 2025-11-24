import duckdb
import pandas as pd
import os
from django.conf import settings
import threading
import time
from contextlib import contextmanager


class ConnectionPool:
    """Simple connection pool for MotherDuck"""

    def __init__(self, token, share, max_connections=5, connection_timeout=30):
        self.token = token
        self.share = share
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self._pool = []
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean up idle connections every 5 minutes

    def _create_connection(self):
        """Create a new MotherDuck connection"""
        return duckdb.connect(f"md:{self.share}?motherduck_token={self.token}")

    @contextmanager
    def get_connection(self):
        """Get a connection from pool with context manager"""
        conn = None
        try:
            with self._lock:
                # Cleanup old idle connections if needed
                if time.time() - self._last_cleanup > self._cleanup_interval:
                    self._cleanup_idle_connections()

                # Try to get from pool
                if self._pool:
                    conn = self._pool.pop()
                else:
                    # Create new connection if pool is empty
                    conn = self._create_connection()

            # Set query timeout
            conn.execute(f"SET statement_timeout = {self.connection_timeout * 1000}")  # milliseconds
            yield conn

        finally:
            # Return connection to pool
            if conn:
                try:
                    with self._lock:
                        if len(self._pool) < self.max_connections:
                            self._pool.append(conn)
                        else:
                            # Pool is full, close connection
                            conn.close()
                except Exception:
                    # If returning fails, just close it
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _cleanup_idle_connections(self):
        """Close idle connections to free resources"""
        # Keep max half the pool size
        target_size = max(1, self.max_connections // 2)
        while len(self._pool) > target_size:
            conn = self._pool.pop()
            try:
                conn.close()
            except Exception:
                pass
        self._last_cleanup = time.time()

    def close_all(self):
        """Close all connections in pool"""
        with self._lock:
            while self._pool:
                conn = self._pool.pop()
                try:
                    conn.close()
                except Exception:
                    pass


class MotherDuckStorage:
    """MotherDuck storage interface"""

    _pool = None
    _pool_lock = threading.Lock()

    def __init__(self):
        self.token = settings.MOTHERDUCK_TOKEN
        self.share = settings.MOTHERDUCK_SHARE
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool (singleton)"""
        if MotherDuckStorage._pool is None:
            with MotherDuckStorage._pool_lock:
                if MotherDuckStorage._pool is None:
                    if not self.token:
                        raise ValueError("MOTHERDUCK_TOKEN not configured in settings")
                    MotherDuckStorage._pool = ConnectionPool(
                        self.token,
                        self.share,
                        max_connections=5,
                        connection_timeout=30
                    )

    def _get_connection(self):
        """Legacy method - returns context manager for backward compatibility"""
        return self._pool.get_connection()
    
    def execute_query(self, schema, query):
        """Execute SQL query and return results"""
        with self._get_connection() as conn:
            conn.execute(f"USE {self.share}")
            conn.execute(f"SET SCHEMA '{schema}'")

            df = conn.execute(query).fetchdf()

            # Convert to dict for JSON serialization
            return {
                'columns': df.columns.tolist(),
                'data': df.values.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'shape': df.shape
            }
    
    def list_tables(self, schema):
        """List tables in schema"""
        with self._get_connection() as conn:
            query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
            ORDER BY table_name
            """
            df = conn.execute(query).fetchdf()
            return df['table_name'].tolist()
    
    def validate_output(self, schema, validation):
        """Validate lesson completion"""
        try:
            with self._get_connection() as conn:
                conn.execute(f"USE {self.share}")
                conn.execute(f"SET SCHEMA '{schema}'")

                result = conn.execute(validation['sql']).fetchdf()

                models_built = result.iloc[0]['models_built']
                success = models_built >= validation['expected_min']

                return {
                    'success': success,
                    'models_built': int(models_built),
                    'expected_min': validation['expected_min']
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }