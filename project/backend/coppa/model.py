"""Database API for FastAPI application."""
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, Generator
from pathlib import Path

# Database configuration
DATABASE_PATH = "var/coppa.sqlite3"

def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row objects to a dictionary keyed on column name.
    
    This is useful for building dictionaries which are then used to render
    responses. Note that this would be inefficient for large queries.
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Open a database connection as a context manager.
    
    This replaces Flask's g object pattern with a proper context manager
    that ensures the connection is always closed.
    
    Usage:
        with get_db() as db:
            result = db.execute("SELECT * FROM users").fetchall()
    """
    db_path = Path(DATABASE_PATH)
    
    # Create directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = dict_factory
    
    # Enable foreign keys (sqlite3 backwards compatibility)
    connection.execute("PRAGMA foreign_keys = ON")
    
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# Alternative: Dependency injection for FastAPI
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for database connection.
    
    Usage in FastAPI routes:
        @app.get("/users")
        def get_users(db: sqlite3.Connection = Depends(get_db_connection)):
            return db.execute("SELECT * FROM users").fetchall()
    """
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = dict_factory
    connection.execute("PRAGMA foreign_keys = ON")
    
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# Utility functions for common database operations
def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a SELECT query and return results."""
    with get_db() as db:
        return db.execute(query, params).fetchall()

def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE query and return rows affected."""
    with get_db() as db:
        cursor = db.execute(query, params)
        return cursor.rowcount

def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute an INSERT query and return the last row ID."""
    with get_db() as db:
        cursor = db.execute(query, params)
        return cursor.lastrowid