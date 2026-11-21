"""
===============================================
  TELEGRAM MUSIC BOT (bot.py)
===============================================
Ye bot Telegram group ke voice chat me gaane bajata hai.
Ye aapki Private Music API se connect hota hai.

Commands:
  /play <gaane ka naam>  - Voice chat me gaana bajao
  /stop                  - Gaana band karo
  /pause                 - Gaana pause karo
  /resume                - Paused gaana dubara chalao
  /ping                  - Bot alive hai ya nahi check karo
  /help                  - Commands ki list

Chalane ka command:
  python bot.py
"""

import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# Config file se settings import karo
from config import (
    BOT_TOKEN, API_ID, API_HASH,
    API_BASE_URL, API_KEY,
    SESSION_NAME
)

# =============================================
# BOT & CALL CLIENT INITIALIZE KARO
# =============================================
# Pyrogram client - Telegram se baat karne ke liye
app = Client(
    SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# PyTgCalls client - Voice chat me audio play karne ke liye
calls = PyTgCalls(app)

# Har group me kya chal raha hai uska track rakhne ke liye
# Format: {chat_id: {"title": "...", "video_id": "..."}}
active_songs = {}


# =============================================
# HELPER FUNCTIONS
# =============================================
def search_song(query: str) -> dict:
    """
    Aapki Music API ke /search endpoint se gaana dhoondhta hai.
    Returns: Song ki details (title, id, thumbnail, etc.) ya None
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/search",
            params={"q": query, "api_key": API_KEY},
            timeout=15  # 15 seconds max wait
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0]  # Pehla result return karo
        
        return None
    
    except requests.RequestException as e:
        print(f"[ERROR] API search failed: {e}")
        return None


def get_stream_url(video_id: str) -> str:
    """
    Gaane ki stream URL banata hai.
    Ye URL directly PyTgCalls ko diya jayega jo isse play karega.
    """
    return f"{API_BASE_URL}/stream/{video_id}?api_key={API_KEY}"


# =============================================
# BOT COMMANDS
# =============================================

@app.on_message(filters.command("play") & filters.group)
async def play_command(client: Client, message: Message):
    """
    /play <gaane ka naam>
    
    Gaana search karke voice chat me play karta hai.
    Example: /play Tum Hi Ho Arijit Singh
    """
    # Check karo ki user ne gaane ka naam likha hai ya nahi
    if len(message.command) < 2:
        await message.reply_text(
            "❌ **Gaane ka naam likhein!**\n"
            "Example: `/play Tum Hi Ho Arijit Singh`"
        )
        return
    
    # Gaane ka naam nikalo (command ke baad ka saara text)
    query = " ".join(message.command[1:])
    
    # User ko batao ki search ho raha hai
    status_msg = await message.reply_text(f"🔍 **Searching:** `{query}`...")
    
    # API se gaana search karo
    song = search_song(query)
    
    if not song:
        await status_msg.edit_text(
            "❌ **Gaana nahi mila!**\n"
            "Kripya doosre keywords try karein."
        )
        return
    
    # Stream URL banao
    video_id = song["id"]
    stream_url = get_stream_url(video_id)
    
    # Status update karo
    await status_msg.edit_text(
        f"🎵 **Now Playing:**\n"
        f"**{song['title']}**\n"
        f"👤 {song.get('channel', 'Unknown')}\n"
        f"⏱ {song.get('duration_string', 'N/A')}"
    )
    
    # Voice chat me gaana play karo
    try:
        chat_id = message.chat.id
        
        await calls.play(
            chat_id,
            MediaStream(stream_url)  # API se audio stream play karo
        )
        
        # Track karo ki is group me kya chal raha hai
        active_songs[chat_id] = {
            "title": song["title"],
            "video_id": video_id,
            "requested_by": message.from_user.first_name
        }
    
    except Exception as e:
        error_msg = str(e)
        
        if "not found" in error_msg.lower() or "no active" in error_msg.lower():
            await message.reply_text(
                "❌ **Voice Chat active nahi hai!**\n"
                "Pehle group me Voice Chat start karein,\n"
                "phir `/play` command use karein."
            )
        else:
            await message.reply_text(
                f"❌ **Play Error:**\n`{error_msg}`"
            )


@app.on_message(filters.command("stop") & filters.group)
async def stop_command(client: Client, message: Message):
    """
    /stop - Voice chat se gaana band karta hai.
    """
    chat_id = message.chat.id
    
    try:
        await calls.leave_call(chat_id)
        
        # Active song hatao
        if chat_id in active_songs:
            del active_songs[chat_id]
        
        await message.reply_text("⏹ **Playback stopped!**")
    
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")


@app.on_message(filters.command("pause") & filters.group)
async def pause_command(client: Client, message: Message):
    """
    /pause - Chal rahe gaane ko pause karta hai.
    """
    try:
        await calls.pause_stream(message.chat.id)
        await message.reply_text("⏸ **Paused!** Resume karne ke liye `/resume` likhein.")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")


@app.on_message(filters.command("resume") & filters.group)
async def resume_command(client: Client, message: Message):
    """
    /resume - Paused gaane ko dubara chalata hai.
    """
    try:
        await calls.resume_stream(message.chat.id)
        await message.reply_text("▶️ **Resumed!**")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")


@app.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """
    /ping - Bot aur API dono alive hain ya nahi check karta hai.
    """
    # API ka status check karo
    try:
        resp = requests.get(f"{API_BASE_URL}/", timeout=5)
        api_status = "🟢 Online" if resp.status_code == 200 else "🔴 Error"
    except Exception:
        api_status = "🔴 Offline"
    
    await message.reply_text(
        f"🏓 **Pong!**\n"
        f"🤖 Bot: 🟢 Online\n"
        f"🎵 Music API: {api_status}"
    )


@app.on_message(filters.command("nowplaying") & filters.group)
async def nowplaying_command(client: Client, message: Message):
    """
    /nowplaying - Abhi kaunsa gaana chal raha hai dikhata hai.
    """
    chat_id = message.chat.id
    
    if chat_id in active_songs:
        song = active_songs[chat_id]
        await message.reply_text(
            f"🎵 **Now Playing:**\n"
            f"**{song['title']}**\n"
            f"🙋 Requested by: {song.get('requested_by', 'Unknown')}"
        )
    else:
        await message.reply_text("🔇 **Abhi koi gaana nahi chal raha.**")


@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """
    /help - Saare commands ki list dikhata hai.
    """
    await message.reply_text(
        "🎵 **Music Bot Commands:**\n\n"
        "▶️ `/play <naam>` - Gaana search karke VC me bajao\n"
        "⏹ `/stop` - Gaana band karo\n"
        "⏸ `/pause` - Gaana pause karo\n"
        "▶️ `/resume` - Paused gaana chalao\n"
        "🎵 `/nowplaying` - Kaunsa gaana chal raha hai\n"
        "🏓 `/ping` - Bot status check\n"
        "❓ `/help` - Ye message\n\n"
        "**Note:** Bot ko group me admin banana zaroori hai\n"
        "aur Voice Chat pehle se start hona chahiye!"
    )


@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """
    /start - Private chat me welcome message.
    """
    await message.reply_text(
        f"👋 **Welcome!**\n\n"
        f"Mai ek Music Bot hoon. Mujhe kisi group me add karo\n"
        f"aur `/play <gaane ka naam>` likhke voice chat me gaana bajao!\n\n"
        f"Commands dekhne ke liye: /help"
    )


# =============================================
# BOT START KARO
# =============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🎵 Telegram Music Bot Starting...")
    print(f"🔗 API: {API_BASE_URL}")
    print("=" * 50)
    
    # PyTgCalls aur Pyrogram dono saath me start karo
    calls.start()
    app.run()
