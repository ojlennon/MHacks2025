"""Database API for FastAPI application - Vercel compatible version."""
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, Generator
from pathlib import Path
import os

# For Vercel deployment, we'll use an in-memory database
# In production, you'd want to use a proper database service like PlanetScale, Supabase, or Vercel Postgres

def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row objects to a dictionary keyed on column name."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Open a database connection as a context manager - Vercel compatible."""
    
    # Use in-memory database for Vercel deployment
    connection = sqlite3.connect(":memory:")
    connection.row_factory = dict_factory
    
    # Enable foreign keys
    connection.execute("PRAGMA foreign_keys = ON")
    
    # Create the table and insert sample data
    connection.execute("""
        CREATE TABLE IF NOT EXISTS lisence_plates(
            plate_number VARCHAR(10) PRIMARY KEY,
            owner_name VARCHAR(100) NOT NULL,
            DOB DATE NOT NULL,
            hasWarrant BOOLEAN DEFAULT FALSE,
            warrant_reason TEXT,
            registration_date DATE DEFAULT CURRENT_DATE,
            isStolen BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Insert sample data
    sample_data = [
        ('ABC123', 'John Doe', '1985-06-15', False, None, '2020-01-10', False),
        ('XYZ789', 'Jane Smith', '1990-11-22', True, 'Unpaid parking tickets', '2019-03-05', False),
        ('LMN456', 'Alice Johnson', '1978-02-28', False, None, '2021-07-19', True),
        ('DEF321', 'Bob Brown', '2000-12-12', True, 'Speeding violations', '2018-09-30', False)
    ]
    
    connection.executemany(
        "INSERT OR IGNORE INTO lisence_plates VALUES (?, ?, ?, ?, ?, ?, ?)",
        sample_data
    )
    
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
    """FastAPI dependency for database connection."""
    with get_db() as conn:
        yield conn

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
