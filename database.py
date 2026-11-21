"""
===============================================
  MUSIC API - DATABASE MANAGEMENT (database.py)
===============================================
Ye file SQLite database ko manage karti hai.
Ismein API keys, user plans, aur usage tracking hota hai.
"""

import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
from config import DATABASE_FILE


def get_db_connection():
    """Database se connection banata hai."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Results ko dictionary jaisa access karne ke liye
    return conn


def init_database():
    """
    Database tables banata hai agar pehle se nahi hain.
    Ye function app start hone par ek baar call hota hai.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # ---- USERS TABLE ----
    # Har API key user ka record yaha store hoga
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Client ka naam (jaise "Rahul Bot", "Aman Music")
            client_name TEXT NOT NULL,
            
            -- Unique API key (ye client ko deni hoti hai)
            api_key TEXT UNIQUE NOT NULL,
            
            -- Plan type: "free", "paid", "unlimited"
            plan_type TEXT NOT NULL DEFAULT 'free',
            
            -- Ek din me kitne requests kar sakta hai
            daily_limit INTEGER NOT NULL DEFAULT 50,
            
            -- Key kab expire hogi (NULL = kabhi expire nahi hogi)
            expires_at TEXT,
            
            -- Key active hai ya band ki gayi hai
            is_active INTEGER NOT NULL DEFAULT 1,
            
            -- Key kab bani
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            
            -- Aaj kitne requests use kiye
            requests_today INTEGER NOT NULL DEFAULT 0,
            
            -- Total kitne requests ab tak kiye
            total_requests INTEGER NOT NULL DEFAULT 0,
            
            -- Aakhri baar counter kab reset hua (daily reset ke liye)
            last_reset_date TEXT NOT NULL DEFAULT (date('now'))
        )
    """)

    # ---- REQUEST LOGS TABLE ----
    # Har ek API request ka log yaha store hoga (analytics ke liye)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Kis user ne request ki
            api_key TEXT NOT NULL,
            
            -- Kaunsa endpoint call hua ("/search" ya "/stream")
            endpoint TEXT NOT NULL,
            
            -- Kya search kiya ya kaunsa video stream kiya
            query TEXT,
            
            -- Request ka timestamp
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DATABASE] Tables initialized successfully!")


def generate_api_key():
    """
    Ek unique random API key generate karta hai.
    Format: "MUS_xxxxxxxxxxxxxxxxxxxxxxxxxxxx" (MUS prefix + 28 random characters)
    """
    random_part = uuid.uuid4().hex + uuid.uuid4().hex[:12]
    return f"MUS_{random_part}"


def create_user(client_name: str, plan_type: str = "free", daily_limit: int = 50, 
                expires_in_days: int = None):
    """
    Naya user/client create karta hai aur uski API key return karta hai.
    
    Args:
        client_name: Client ka naam (jaise "Rahul Music Bot")
        plan_type: "free", "paid", ya "unlimited"
        daily_limit: Daily kitne requests allow hain
        expires_in_days: Kitne dinon me key expire hogi (None = never)
    
    Returns:
        dict: Naye user ki details (api_key, plan, expiry, etc.)
    """
    conn = get_db_connection()
    api_key = generate_api_key()
    
    # Expiry date calculate karo agar set ki gayi hai
    expires_at = None
    if expires_in_days:
        expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
    
    try:
        conn.execute(
            """INSERT INTO users (client_name, api_key, plan_type, daily_limit, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (client_name, api_key, plan_type, daily_limit, expires_at)
        )
        conn.commit()
        return {
            "client_name": client_name,
            "api_key": api_key,
            "plan_type": plan_type,
            "daily_limit": daily_limit,
            "expires_at": expires_at,
            "message": "User created successfully!"
        }
    except sqlite3.IntegrityError:
        return {"error": "API key generation conflict. Please try again."}
    finally:
        conn.close()


def validate_api_key(api_key: str):
    """
    API key ko validate karta hai:
    1. Key database me exist karti hai ya nahi
    2. Key active hai ya revoke ki gayi hai
    3. Key expire toh nahi ho gayi
    4. Daily limit cross toh nahi ho gayi
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None, user_row: dict or None)
    """
    conn = get_db_connection()
    
    user = conn.execute(
        "SELECT * FROM users WHERE api_key = ?", (api_key,)
    ).fetchone()
    
    if not user:
        conn.close()
        return False, "Invalid API key. Access denied.", None
    
    # Check: Key active hai ya nahi
    if not user['is_active']:
        conn.close()
        return False, "This API key has been revoked/disabled.", None
    
    # Check: Key expire toh nahi ho gayi
    if user['expires_at']:
        expiry = datetime.fromisoformat(user['expires_at'])
        if datetime.now() > expiry:
            conn.close()
            return False, "This API key has expired. Please renew.", None
    
    # Check: Daily limit reset karna hai ya nahi
    today = datetime.now().strftime('%Y-%m-%d')
    if user['last_reset_date'] != today:
        # Naya din hai - counter reset karo
        conn.execute(
            "UPDATE users SET requests_today = 0, last_reset_date = ? WHERE api_key = ?",
            (today, api_key)
        )
        conn.commit()
        # Updated user fetch karo
        user = conn.execute(
            "SELECT * FROM users WHERE api_key = ?", (api_key,)
        ).fetchone()
    
    # Check: Daily limit cross toh nahi ho gayi
    if user['requests_today'] >= user['daily_limit']:
        conn.close()
        return False, f"Daily limit ({user['daily_limit']}) reached. Try again tomorrow.", None
    
    conn.close()
    return True, None, dict(user)


def increment_usage(api_key: str, endpoint: str, query: str = None):
    """
    Har successful request ke baad usage counter badhata hai
    aur request log me entry karta hai.
    """
    conn = get_db_connection()
    
    # User ke counters update karo
    conn.execute(
        """UPDATE users 
           SET requests_today = requests_today + 1,
               total_requests = total_requests + 1
           WHERE api_key = ?""",
        (api_key,)
    )
    
    # Request log me entry daalo
    conn.execute(
        "INSERT INTO request_logs (api_key, endpoint, query) VALUES (?, ?, ?)",
        (api_key, endpoint, query)
    )
    
    conn.commit()
    conn.close()


def revoke_api_key(api_key: str):
    """API key ko band/disable karta hai."""
    conn = get_db_connection()
    result = conn.execute(
        "UPDATE users SET is_active = 0 WHERE api_key = ?", (api_key,)
    )
    conn.commit()
    affected = result.rowcount
    conn.close()
    
    if affected > 0:
        return {"message": f"API key revoked successfully.", "api_key": api_key}
    return {"error": "API key not found."}


def get_all_users():
    """Saare registered users ki list return karta hai."""
    conn = get_db_connection()
    users = conn.execute(
        """SELECT client_name, api_key, plan_type, daily_limit, 
                  requests_today, total_requests, is_active, 
                  expires_at, created_at 
           FROM users ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]


def get_stats():
    """Admin dashboard ke liye overall statistics return karta hai."""
    conn = get_db_connection()
    
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]
    total_requests = conn.execute("SELECT COALESCE(SUM(total_requests), 0) FROM users").fetchone()[0]
    today_requests = conn.execute("SELECT COALESCE(SUM(requests_today), 0) FROM users").fetchone()[0]
    
    # Plan-wise breakdown
    plan_stats = conn.execute(
        """SELECT plan_type, COUNT(*) as count 
           FROM users WHERE is_active = 1 
           GROUP BY plan_type"""
    ).fetchall()
    
    # Recent 10 requests
    recent = conn.execute(
        """SELECT api_key, endpoint, query, created_at 
           FROM request_logs 
           ORDER BY created_at DESC LIMIT 10"""
    ).fetchall()
    
    conn.close()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_requests_all_time": total_requests,
        "total_requests_today": today_requests,
        "plan_breakdown": {row['plan_type']: row['count'] for row in plan_stats},
        "recent_requests": [dict(r) for r in recent]
    }
