import sqlite3
import os
from app.core.config import DATABASE_URL, IS_POSTGRES, DB_PATH

def get_db():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return conn, cursor
    else:
        os.makedirs(DB_PATH.parent, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return conn, cursor

def qp(query: str) -> str:
    if IS_POSTGRES:
        return query.replace("?", "%s")
    return query

def init_db():
    conn, cursor = get_db()
    
    if IS_POSTGRES:
        # Create predictions table in Postgres (with box column built-in)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            date TEXT,
            time TEXT,
            image TEXT,
            image_name TEXT,
            status TEXT,
            confidence REAL,
            title TEXT,
            findings TEXT, -- JSON array
            actions TEXT,  -- JSON array
            reviewed INTEGER DEFAULT 0,
            flagged INTEGER DEFAULT 0,
            model_version TEXT,
            analysis_time TEXT,
            box TEXT
        );
        """)
    else:
        # Create predictions table in SQLite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            date TEXT,
            time TEXT,
            image TEXT,
            image_name TEXT,
            status TEXT,
            confidence REAL,
            title TEXT,
            findings TEXT, -- JSON array
            actions TEXT,  -- JSON array
            reviewed INTEGER DEFAULT 0,
            flagged INTEGER DEFAULT 0,
            model_version TEXT,
            analysis_time TEXT
        );
        """)
        # Add box column if it doesn't exist dynamically
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN box TEXT;")
        except sqlite3.OperationalError:
            pass
            
    # Create notifications table
    cursor.execute(qp("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        title TEXT,
        message TEXT,
        type TEXT,
        time TEXT,
        read INTEGER DEFAULT 0
    );
    """))
    
    if not IS_POSTGRES:
        conn.commit()
    conn.close()
