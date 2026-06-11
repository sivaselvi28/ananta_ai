"""
query_executor.py — Executes a SELECT query against a SQLite database
using a read-only connection so no write operations can slip through.
"""

import sqlite3
import pandas as pd


def execute_query(db_path: str, sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Execute a SELECT query on the given SQLite database.

    Opens a read-only URI connection to prevent any accidental writes.

    Returns:
        (DataFrame, None)        on success
        (None, error_message)    on failure
    """
    try:
        # Read-only mode via URI — raises an error if the file doesn't exist
        uri  = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        df   = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as exc:
        return None, str(exc)
