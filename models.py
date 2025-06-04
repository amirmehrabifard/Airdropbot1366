import sqlite3

DB_FILE = "bot_db.sqlite3"

def setup_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        invite_code TEXT UNIQUE,
        inviter_id INTEGER,
        wallet_address TEXT,
        rewarded INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invite_rewards (
        inviter_id INTEGER,
        invited_id INTEGER,
        PRIMARY KEY(inviter_id, invited_id)
    )''')
    conn.commit()
    conn.close()

def add_user(user_id: int, invite_code: str, inviter_id: int = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, invite_code, inviter_id) VALUES (?, ?, ?)", (user_id, invite_code, inviter_id))
    conn.commit()
    conn.close()

def get_user_by_id(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, invite_code, inviter_id, wallet_address FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res

def get_user_by_invite_code(invite_code: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, invite_code, inviter_id FROM users WHERE invite_code=?", (invite_code,))
    res = c.fetchone()
    conn.close()
    return res

def save_wallet_address(user_id: int, wallet_address: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET wallet_address=? WHERE user_id=?", (wallet_address, user_id))
    conn.commit()
    conn.close()

def get_wallet_address(user_id: int) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT wallet_address FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    if res:
        return res[0]
    return None

def is_invite_rewarded(inviter_id: int, invited_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM invite_rewards WHERE inviter_id=? AND invited_id=?", (inviter_id, invited_id))
    res = c.fetchone()
    conn.close()
    return bool(res)

def mark_invite_rewarded(inviter_id: int, invited_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO invite_rewards (inviter_id, invited_id) VALUES (?, ?)", (inviter_id, invited_id))
    conn.commit()
    conn.close()
