import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            tickets_bought INTEGER DEFAULT 0,
            wins_count INTEGER DEFAULT 0,
            total_won_stars INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_stars', 0)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_profit', 0)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('goal_stars', 100)")
    conn.commit()
    conn.close()

def add_participant(user_id: int, username: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO participants (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("""
        INSERT INTO users (user_id, username, tickets_bought) 
        VALUES (?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET 
            tickets_bought = tickets_bought + 1,
            username = excluded.username
    """, (user_id, username))
    conn.commit()
    conn.close()

def get_participants():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM participants")
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_participants():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participants")
    conn.commit()
    conn.close()

def get_total_stars():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'total_stars'")
    val = cursor.fetchone()[0]
    conn.close()
    return val

def add_stars(amount: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = value + ? WHERE key = 'total_stars'", (amount,))
    conn.commit()
    conn.close()

def reset_stars():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = 0 WHERE key = 'total_stars'")
    conn.commit()
    conn.close()

def get_goal_stars():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'goal_stars'")
    val = cursor.fetchone()[0]
    conn.close()
    return val

def set_goal_stars(amount: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'goal_stars'", (amount,))
    conn.commit()
    conn.close()

def add_admin_profit(amount: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = value + ? WHERE key = 'admin_profit'", (amount,))
    conn.commit()
    conn.close()

def get_admin_profit():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_profit'")
    val = cursor.fetchone()[0]
    conn.close()
    return val

def record_win(user_id: int, prize: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET wins_count = wins_count + 1, total_won_stars = total_won_stars + ? 
        WHERE user_id = ?
    """, (prize, user_id))
    conn.commit()
    conn.close()

def get_user_stats(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT tickets_bought, wins_count, total_won_stars FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row or (0, 0, 0)

def get_total_users_count():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count
