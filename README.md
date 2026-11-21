# 🎵 Private Music Streaming API + Telegram Bot

Production-ready YouTube audio streaming API jise aap doosre Telegram bot developers ko bech sakte hain.

---

## 📁 Project Structure

```
music-api/
├── config.py            # API ki saari settings (keys, proxy, cache)
├── database.py          # SQLite database management (users, logs)
├── main.py              # FastAPI server (saare endpoints)
├── requirements.txt     # Python libraries
├── test_client.py       # API testing script
├── cookies.txt          # YouTube cookies (aapko banana hai)
├── api_database.db      # Auto-generated database (chhuna nahi hai)
│
└── telegram-bot/        # Telegram Music Bot
    ├── config.py        # Bot ki settings (token, API key)
    ├── bot.py           # Bot ka main code
    └── requirements.txt # Bot ki libraries
```

---

## 🚀 PART 1: API Setup (Ubuntu VPS par)

### Step 1: VPS me Login karke Packages Install Karo

```bash
# System update karo
sudo apt update && sudo apt upgrade -y

# Zaroori packages install karo
sudo apt install python3 python3-pip python3-venv ffmpeg git -y
```

### Step 2: Project Upload/Clone Karo

```bash
# Home directory me jao
cd ~

# Project folder banao (ya git clone karo)
mkdir music-api
cd music-api
```

Ab apne local PC se saari files VPS par upload karo (FileZilla ya scp se),
ya directly VPS me `nano` se files create karo:
```bash
nano config.py       # Paste karo aur Ctrl+O, Enter, Ctrl+X se save karo
nano database.py
nano main.py
nano requirements.txt
```

### Step 3: Python Virtual Environment Banao

```bash
# Virtual environment banao
python3 -m venv venv

# Activate karo
source venv/bin/activate

# Libraries install karo
pip install -r requirements.txt
```

### Step 4: Config Settings Update Karo

`config.py` file kholein aur ye cheezein badlein:

```bash
nano config.py
```

**Zaroori changes:**
1. `ADMIN_SECRET_KEY` = Ek strong random password rakhein (jaise: `"MyStr0ng@dm1nK3y2024"`)
2. `PROXY_URL` = Agar residential proxy hai toh dalein, warna `None` rehne dein

### Step 5: YouTube Cookies Lagao (Bohot Important!)

Cloud server par YouTube aksar block kar deta hai. Cookies lagane se ye problem solve hoti hai:

1. **Chrome browser me extension install karo:**
   - Chrome Web Store se **"Get cookies.txt LOCALLY"** extension install karo
   
2. **Cookies export karo:**
   - YouTube.com kholein aur kisi account se login karo
   - Extension ke icon par click karo
   - "Export" par click karo
   - File save hogi `cookies.txt` naam se

3. **File VPS par upload karo:**
   ```bash
   # FileZilla se upload karo ya scp use karo:
   scp cookies.txt root@YOUR_VPS_IP:~/music-api/
   ```

### Step 6: Server Test Karo (Manual Start)

```bash
# Virtual environment activate karo (agar nahi hai)
source venv/bin/activate

# Server start karo
uvicorn main:app --host 0.0.0.0 --port 8000
```

Ab browser me kholein: `http://YOUR_VPS_IP:8000/`
Agar `{"status": "🟢 online"}` dikhe toh sab sahi hai!

**Server band karne ke liye:** `Ctrl + C`

### Step 7: 24/7 Background Service Banao (Systemd)

Taaki terminal band hone par bhi API chalti rahe:

```bash
sudo nano /etc/systemd/system/musicapi.service
```

Ye content paste karo:
```ini
[Unit]
Description=Music Streaming API Service
After=network.target

[Service]
# IMPORTANT: Agar aapka username root nahi hai toh badal dein
User=root
WorkingDirectory=/root/music-api
ExecStart=/root/music-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

# Environment variables (optional - config.py me bhi set kar sakte hain)
# Environment=ADMIN_SECRET_KEY=MyStr0ng@dm1nK3y2024
# Environment=PROXY_URL=http://user:pass@proxy:port

[Install]
WantedBy=multi-user.target
```

Save karo (Ctrl+O, Enter, Ctrl+X) aur service start karo:

```bash
sudo systemctl daemon-reload
sudo systemctl start musicapi
sudo systemctl enable musicapi    # Boot par auto-start

# Status check karo
sudo systemctl status musicapi
```

**Useful commands:**
```bash
sudo systemctl restart musicapi   # Restart karo
sudo systemctl stop musicapi      # Band karo
journalctl -u musicapi -f         # Live logs dekho
```

---

## 🔑 PART 2: API Keys Manage Karo

### Apne liye Unlimited Key Banao

Browser me ye URL kholein (apni admin key aur server IP dalein):

```
http://YOUR_IP:8000/admin/create-key?client_name=My+Personal+Bot&plan=unlimited&admin_key=YOUR_ADMIN_KEY
```

### Client ke liye Paid Key Banao (30 din expiry, 500 daily limit)

```
http://YOUR_IP:8000/admin/create-key?client_name=Rahul+Music+Bot&plan=paid&daily_limit=500&expires_days=30&admin_key=YOUR_ADMIN_KEY
```

### Client ki Key Band Karo

```
http://YOUR_IP:8000/admin/revoke-key?api_key=MUS_xxxxx&admin_key=YOUR_ADMIN_KEY
```

### Saare Users Dekho

```
http://YOUR_IP:8000/admin/users?admin_key=YOUR_ADMIN_KEY
```

### Statistics Dekho

```
http://YOUR_IP:8000/admin/stats?admin_key=YOUR_ADMIN_KEY
```

### Interactive API Docs (Swagger UI)

```
http://YOUR_IP:8000/docs
```

Yaha par saare endpoints try kar sakte hain browser me hi!

---

## 🎵 PART 3: API Use Kaise Karein (Client Guide)

### Search Song
```
GET http://YOUR_IP:8000/search?q=Believer&api_key=MUS_xxxxx
```

### Stream Audio (IP-Lock Bypass)
```
GET http://YOUR_IP:8000/stream/VIDEO_ID?api_key=MUS_xxxxx
```
Is URL ko directly Telegram bot me PyTgCalls ko de sakte hain.

### Get Video Info
```
GET http://YOUR_IP:8000/info/VIDEO_ID?api_key=MUS_xxxxx
```

---

## 🤖 PART 4: Telegram Bot Setup

### Step 1: Bot Credentials Lao

1. **Bot Token:** Telegram me @BotFather ko message karo → `/newbot` → Naam aur username do → Token milega
2. **API ID & Hash:** https://my.telegram.org par jao → Login karo → "API development tools" → App banao → API ID aur Hash milega

### Step 2: Bot Files Setup Karo

```bash
cd ~/music-api/telegram-bot

# Virtual environment banao
python3 -m venv venv
source venv/bin/activate

# Libraries install karo
pip install -r requirements.txt
```

### Step 3: Bot Config Update Karo

```bash
nano config.py
```

Ye values bharein:
- `BOT_TOKEN` = BotFather se mila hua token
- `API_ID` = my.telegram.org se mila hua number
- `API_HASH` = my.telegram.org se mili hui string
- `API_BASE_URL` = Aapki API ka URL (jaise `"http://localhost:8000"`)
- `API_KEY` = Admin se bani unlimited API key

### Step 4: Bot Background Service Banao

```bash
sudo nano /etc/systemd/system/musicbot.service
```

Paste karo:
```ini
[Unit]
Description=Telegram Music Bot Service
After=network.target musicapi.service

[Service]
User=root
WorkingDirectory=/root/music-api/telegram-bot
ExecStart=/root/music-api/telegram-bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Start karo:
```bash
sudo systemctl daemon-reload
sudo systemctl start musicbot
sudo systemctl enable musicbot

# Status check
sudo systemctl status musicbot
```

### Step 5: Bot Test Karo

1. Telegram me apne bot ko search karo aur `/start` bhejo
2. Bot ko kisi group me add karo aur **Admin banao**
3. Group me Voice Chat start karo
4. `/play Tum Hi Ho` likho — gaana bajne lagega! 🎵

---

## ⚠️ Troubleshooting (Common Problems)

| Problem | Solution |
|---------|----------|
| `Sign in to confirm you're not a bot` | `cookies.txt` file update karo (naye cookies export karo) |
| `HTTP Error 429: Too Many Requests` | Proxy use karo ya cookies rotate karo |
| `yt-dlp ExtractorError` | yt-dlp update karo: `pip install -U yt-dlp` |
| Bot Voice Chat join nahi kar raha | Bot ko group me Admin banao |
| `quotaExceeded` | Daily limit badha do ya naye din ka wait karo |
| API key expired | Admin se nayi key banwao |

---

## 🔄 Regular Maintenance

Ye commands har 2-3 hafte me ek baar zaroor chalao:

```bash
# yt-dlp update karo (YouTube changes ke liye)
cd ~/music-api
source venv/bin/activate
pip install -U yt-dlp

# API restart karo
sudo systemctl restart musicapi

# Bot bhi restart karo
sudo systemctl restart musicbot

# Cookies bhi 1-2 mahine me refresh kar dein
```

---

## 📞 Client ko Kya Dena Hai (Jab API Bechein)

Jab koi client aapki API khareedna chahe, usko ye cheezein dein:

1. **API Base URL:** `http://YOUR_IP:8000`
2. **API Key:** Admin panel se generate ki hui key
3. **Endpoints documentation:** Ye README ya Swagger UI link (`/docs`)
4. **Daily Limit info:** Kitne requests kar sakta hai per day
5. **Expiry info:** Key kab tak valid hai

**Pricing Example:**
- Free Plan: 50 requests/day (trial ke liye)
- Basic Plan: 500 requests/day @ ₹299/month
- Pro Plan: 2000 requests/day @ ₹799/month
- Unlimited Plan: No limit @ ₹1499/month
