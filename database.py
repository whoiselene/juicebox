import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "papaya.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS cover_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                company_name TEXT NOT NULL,
                original_text TEXT NOT NULL,
                cleaned_text TEXT NOT NULL,
                robot_score REAL NOT NULL,
                clichés_found TEXT 
            );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_company_name ON cover_letters (company_name);")
    finally:
        conn.close()

def save_cover_letter(company_name, original_text, cleaned_text, robot_score, clichés_found):
    """
    Saves a rewritten cover letter entry.
    clichés_found should be a Python list or dict, which is serialized as JSON in the DB.
    """
    conn = get_connection()
    try:
        cliches_json = json.dumps(clichés_found)
        with conn:
            cursor = conn.execute("""
            INSERT INTO cover_letters (company_name, original_text, cleaned_text, robot_score, clichés_found)
            VALUES (?, ?, ?, ?, ?)
            """, (company_name, original_text, cleaned_text, robot_score, cliches_json))
            return cursor.lastrowid
    finally:
        conn.close()

def get_all_entries():
    """Retrieves all cover letter entries ordered by timestamp descending."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
        SELECT id, timestamp, company_name, original_text, cleaned_text, robot_score, clichés_found 
        FROM cover_letters 
        ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        entries = []
        for r in rows:
            try:
                cliches = json.loads(r["clichés_found"])
            except Exception:
                cliches = []
            entries.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "company_name": r["company_name"],
                "original_text": r["original_text"],
                "cleaned_text": r["cleaned_text"],
                "robot_score": r["robot_score"],
                "clichés_found": cliches
            })
        return entries
    finally:
        conn.close()

def delete_entry(entry_id):
    """Deletes an entry from the database by ID."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM cover_letters WHERE id = ?", (entry_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()
