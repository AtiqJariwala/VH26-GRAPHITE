"""Safe database handling with context manager."""

import sqlite3

def query_users():
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
    return results  # Safe: context manager handles close
