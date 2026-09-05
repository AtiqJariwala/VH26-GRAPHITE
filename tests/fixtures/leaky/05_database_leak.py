"""Database connection leak."""

import sqlite3

def query_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    return results  # LEAK: connection never closed
