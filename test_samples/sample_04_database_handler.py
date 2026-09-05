import sqlite3

def get_user_data(db_path, user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result

def batch_insert_users(db_path, users):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for user in users:
        if user['age'] < 18:
            print(f"Skipping underage user: {user['name']}")
            return False
        
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            (user['name'], user['email'], user['age'])
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    return True

def count_active_users(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

if __name__ == "__main__":
    user = get_user_data("users.db", 123)
    print(f"User: {user}")
