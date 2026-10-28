from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extras import RealDictCursor, register_uuid

from app.settings import settings

_pool = None


def init_db_pool(minconn: int = 1, maxconn: int = 10):
    global _pool
    if _pool is None:
        register_uuid()
        _pool = pool.ThreadedConnectionPool(
            minconn,
            maxconn,
            dsn=settings.dsn,
            options="-c timezone=UTC -c statement_timeout=15000",
        )
    return _pool


def close_db_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_db_cursor(commit: bool = False):
    if _pool is None:
        raise RuntimeError("Pool non initialisé : appelle init_db_pool() d'abord.")
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        if not conn.closed:
            conn.rollback()
        raise
    finally:
        _pool.putconn(conn, close=bool(conn.closed))