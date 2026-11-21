"""
===============================================
  MUSIC API - CONFIGURATION FILE (config.py)
===============================================
Yaha par aapko apni API ki saari settings karni hain.
Har setting ke saath Hindi comment diya hai taaki samajhne me aasani ho.
"""

import os

# =============================================
# 1. ADMIN SECRET KEY
# =============================================
# Ye aapki MASTER key hai. Isse aap naye clients bana sakte hain,
# keys revoke kar sakte hain, aur stats dekh sakte hain.
# IMPORTANT: Isko ek strong random string me badal dein!
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "fpO4PThOuoxcNTR3d-A3Rd0rb_unZibPCD2KltsYbDU")

# =============================================
# 2. YOUTUBE COOKIES FILE
# =============================================
# Cloud server par YouTube "Sign in to confirm" error de sakta hai.
# Usse bachne ke liye apne browser se cookies export karke
# 'cookies.txt' naam ki file is folder me rakh dein.
# Agar file nahi hai toh None rehne dein - API bina cookies ke bhi chalegi.
COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

# =============================================
# 3. PROXY CONFIGURATION (Optional)
# =============================================
# Agar aapke server ki IP YouTube ne block kar di hai,
# toh residential proxy ka URL yaha dalein.
# Format: "http://username:password@proxy_ip:port"
# Jaise: "http://user123:pass456@103.21.45.67:8080"
# Agar proxy nahi use karni toh None chhod dein.
PROXY_URL = os.getenv("PROXY_URL", None)

# =============================================
# 4. DATABASE FILE PATH
# =============================================
# SQLite database file ka naam. Ismein saare API keys,
# usage stats, aur client data store hoga.
DATABASE_FILE = "api_database.db"

# =============================================
# 5. IN-MEMORY CACHE SETTINGS
# =============================================
# Ek baar search ya stream info fetch hone ke baad
# kitni der tak cache me rakhe (seconds me).
# Default: 3600 seconds = 1 ghanta
CACHE_TTL_SECONDS = 3600

# Maximum kitne items cache me rakhne hain.
# Zyada rakhenge toh RAM zyada lagegi.
CACHE_MAX_SIZE = 500

# =============================================
# 6. SERVER SETTINGS
# =============================================
# Server kis port par chalega
SERVER_PORT = 8000

# Kitne worker processes chalayenge (VPS ke CPU cores ke hisab se rakhein)
# 1-2 cores wale VPS ke liye: 2
# 4 cores wale VPS ke liye: 4
SERVER_WORKERS = 2

# =============================================
# 7. DEFAULT PLAN LIMITS
# =============================================
# Naye Free plan user ko daily kitne requests milenge
FREE_PLAN_DAILY_LIMIT = 50

# Naye Paid plan user ko daily kitne requests milenge
PAID_PLAN_DAILY_LIMIT = 500

# Unlimited plan ke liye (koi limit nahi)
UNLIMITED_PLAN_DAILY_LIMIT = 999999
