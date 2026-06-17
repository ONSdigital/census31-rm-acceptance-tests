import contextlib

import psycopg2

from config import Config


@contextlib.contextmanager
def open_cursor(db_host=Config.DB_HOST_CASE, extra_options=""):
    conn = psycopg2.connect(f"dbname='{Config.DB_NAME}' user='{Config.DB_USERNAME}' host='{db_host}' "
                            f"password='{Config.DB_PASSWORD}' port='{Config.DB_PORT}'"
                            f"{Config.DB_CASE_CERTIFICATES}{extra_options}")
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
