"""
===============================================
  TELEGRAM MUSIC BOT - CONFIG (config.py)
===============================================
Yaha par apne Telegram Bot aur API ki details bharein.
Har field ke saath Hindi comment hai taaki samajhne me aasani ho.
"""

# =============================================
# 1. TELEGRAM BOT CREDENTIALS
# =============================================
# BotFather (@BotFather on Telegram) se bot banayen aur token yaha dalein.
# Format: "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
BOT_TOKEN = "YAHA_APNA_BOT_TOKEN_DALEIN"

# Telegram API credentials - https://my.telegram.org par jaake
# "API development tools" me jaake App banayein.
# Waha se API_ID (number) aur API_HASH (string) milega.
API_ID = 12345678                       # <-- Apna API ID dalein (number)
API_HASH = "YAHA_APNA_API_HASH_DALEIN"  # <-- Apna API Hash dalein (string)

# =============================================
# 2. MUSIC API CONNECTION
# =============================================
# Aapki Music Streaming API ka URL.
# Agar bot aur API same server par hain: "http://localhost:8000"
# Agar alag server par hain: "http://API_SERVER_IP:8000"
API_BASE_URL = "http://localhost:8000"

# Aapki API key (admin ya unlimited plan wali key dalein)
# Ye key aapne /admin/create-key se banayi hogi
API_KEY = "YAHA_APNI_API_KEY_DALEIN"

# =============================================
# 3. BOT SETTINGS
# =============================================
# Bot ka naam (logs me dikhega)
BOT_NAME = "MusicBot"

# Bot session ka naam (login session file ka naam)
SESSION_NAME = "music_bot_session"
