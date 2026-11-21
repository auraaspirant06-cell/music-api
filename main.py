"""
===============================================
  MUSIC API - MAIN SERVER (main.py)
===============================================
Ye aapki main Music Streaming API hai.
Starlette + yt-dlp + httpx ka use karke bani hai.
Pydantic ki zaroorat nahi - Python 3.15 par bina kisi error ke chalegi.

Chalane ka command:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import json
import time
import asyncio
from collections import OrderedDict
from urllib.parse import parse_qs

import httpx
import yt_dlp
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse

# Apni config aur database files import karo
from config import (
    ADMIN_SECRET_KEY, COOKIES_FILE, PROXY_URL,
    CACHE_TTL_SECONDS, CACHE_MAX_SIZE,
    FREE_PLAN_DAILY_LIMIT, PAID_PLAN_DAILY_LIMIT, UNLIMITED_PLAN_DAILY_LIMIT
)
from database import (
    init_database, validate_api_key, increment_usage,
    create_user, revoke_api_key, get_all_users, get_stats
)

# =============================================
# IN-MEMORY CACHE (Redis ka free alternative)
# =============================================
class SimpleCache:
    """
    Simple in-memory cache jo TTL (time-to-live) support karta hai.
    Same gaane ko baar-baar YouTube se fetch nahi karega.
    """
    def __init__(self, max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def get(self, key: str):
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self._ttl:
                return entry['data']
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data):
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[key] = {'data': data, 'timestamp': time.time()}

    def clear(self):
        self._cache.clear()

    @property
    def size(self):
        return len(self._cache)


cache = SimpleCache()


# =============================================
# HELPER FUNCTIONS
# =============================================
def get_ydl_options(format_type: str = "bestaudio"):
    """yt-dlp ke configuration options banata hai."""
    opts = {
        'format': f'{format_type}/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'no_check_certificates': True,
    }
    if COOKIES_FILE:
        opts['cookiefile'] = COOKIES_FILE
    if PROXY_URL:
        opts['proxy'] = PROXY_URL
    return opts


def get_api_key(request: Request) -> str:
    """Request se API key nikalta hai (header ya query param se)."""
    # Pehle header me check karo
    key = request.headers.get("x-api-key")
    if key:
        return key
    # Phir query params me check karo
    key = request.query_params.get("api_key")
    return key


def verify_client(request: Request):
    """
    Client ki API key validate karta hai.
    Returns: (user_dict, error_response)
    Agar valid hai toh user_dict milega, warna error_response milega.
    """
    token = get_api_key(request)
    if not token:
        return None, JSONResponse(
            {"error": "API key missing. 'x-api-key' header ya '?api_key=xxx' query param bhejein."},
            status_code=401
        )
    
    is_valid, error_msg, user_data = validate_api_key(token)
    if not is_valid:
        return None, JSONResponse({"error": error_msg}, status_code=403)
    
    return user_data, None


def verify_admin(request: Request):
    """Admin key verify karta hai."""
    token = request.headers.get("x-admin-key") or request.query_params.get("admin_key")
    if token != ADMIN_SECRET_KEY:
        return JSONResponse({"error": "Invalid admin key. Access denied."}, status_code=403)
    return None


# =============================================
# ENDPOINTS
# =============================================

async def home(request: Request):
    """Server status check."""
    return JSONResponse({
        "status": "🟢 online",
        "api_name": "Private Music Streaming API",
        "version": "2.0.0",
        "endpoints": {
            "search": "/search?q=SONG_NAME&api_key=YOUR_KEY",
            "stream": "/stream/VIDEO_ID?api_key=YOUR_KEY",
            "info": "/info/VIDEO_ID?api_key=YOUR_KEY",
        }
    })


async def search_song(request: Request):
    """
    🔍 Gaana search karo.
    Usage: /search?q=Arijit+Singh+Tum+Hi+Ho&api_key=YOUR_KEY
    """
    user, error = verify_client(request)
    if error:
        return error

    q = request.query_params.get("q")
    if not q:
        return JSONResponse({"error": "Query parameter 'q' missing. Example: /search?q=song+name"}, status_code=400)

    limit = int(request.query_params.get("limit", "1"))
    limit = max(1, min(limit, 10))

    # Cache check
    cache_key = f"search:{q}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        increment_usage(user['api_key'], "/search", q)
        return JSONResponse({"source": "cache", "results": cached})

    # YouTube se search karo
    ydl_opts = get_ydl_options()

    try:
        loop = asyncio.get_event_loop()

        def _search():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch{limit}:{q}", download=False)

        info = await loop.run_in_executor(None, _search)

        if not info or 'entries' not in info or not info['entries']:
            return JSONResponse({"error": "Koi gaana nahi mila."}, status_code=404)

        results = []
        for video in info['entries']:
            if video:
                results.append({
                    "id": video.get("id"),
                    "title": video.get("title"),
                    "duration": video.get("duration"),
                    "duration_string": video.get("duration_string"),
                    "thumbnail": video.get("thumbnail"),
                    "channel": video.get("uploader") or video.get("channel"),
                    "view_count": video.get("view_count"),
                    "stream_url": f"/stream/{video.get('id')}",
                })

        cache.set(cache_key, results)
        increment_usage(user['api_key'], "/search", q)
        return JSONResponse({"source": "youtube", "results": results})

    except Exception as e:
        return JSONResponse({"error": f"Search error: {str(e)}"}, status_code=500)


async def get_video_info(request: Request):
    """
    ℹ️ Video ki detailed info.
    Usage: /info/VIDEO_ID?api_key=YOUR_KEY
    """
    user, error = verify_client(request)
    if error:
        return error

    video_id = request.path_params["video_id"]

    cache_key = f"info:{video_id}"
    cached = cache.get(cache_key)
    if cached:
        increment_usage(user['api_key'], "/info", video_id)
        return JSONResponse({"source": "cache", "info": cached})

    ydl_opts = get_ydl_options()
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(video_url, download=False)

        info = await loop.run_in_executor(None, _extract)

        result = {
            "id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "duration_string": info.get("duration_string"),
            "thumbnail": info.get("thumbnail"),
            "channel": info.get("uploader") or info.get("channel"),
            "view_count": info.get("view_count"),
            "upload_date": info.get("upload_date"),
            "description": (info.get("description") or "")[:500],
        }

        cache.set(cache_key, result)
        increment_usage(user['api_key'], "/info", video_id)
        return JSONResponse({"source": "youtube", "info": result})

    except Exception as e:
        return JSONResponse({"error": f"Info extraction error: {str(e)}"}, status_code=500)


async def stream_audio(request: Request):
    """
    🎵 Audio stream (IP-lock bypass).
    YouTube audio ko server ke through pipe karta hai.
    Usage: /stream/VIDEO_ID?api_key=YOUR_KEY
    """
    user, error = verify_client(request)
    if error:
        return error

    video_id = request.path_params["video_id"]

    # Cache me stream URL check karo
    cache_key = f"stream_url:{video_id}"
    audio_url = cache.get(cache_key)

    if not audio_url:
        ydl_opts = get_ydl_options("bestaudio")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            loop = asyncio.get_event_loop()

            def _get_stream_url():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    return info.get("url")

            audio_url = await loop.run_in_executor(None, _get_stream_url)

            if not audio_url:
                return JSONResponse(
                    {"error": "Audio stream URL nahi mila. Video available nahi hai."},
                    status_code=404
                )

            cache.set(cache_key, audio_url)

        except Exception as e:
            return JSONResponse({"error": f"Stream extraction error: {str(e)}"}, status_code=500)

    increment_usage(user['api_key'], "/stream", video_id)

    # Audio proxy - chunk by chunk stream pipe
    async def audio_chunk_generator():
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=30.0),
                follow_redirects=True
            ) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                    "Range": "bytes=0-",
                }
                async with client.stream("GET", audio_url, headers=headers) as response:
                    if response.status_code not in (200, 206):
                        return
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk
        except Exception:
            return

    return StreamingResponse(
        audio_chunk_generator(),
        media_type="audio/webm",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="{video_id}.webm"',
        }
    )


async def direct_url(request: Request):
    """
    🔗 Direct audio URL return karta hai (IP-locked hota hai).
    Usage: /direct-url/VIDEO_ID?api_key=YOUR_KEY
    """
    user, error = verify_client(request)
    if error:
        return error

    video_id = request.path_params["video_id"]
    ydl_opts = get_ydl_options("bestaudio")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    "title": info.get("title"),
                    "direct_audio_url": info.get("url"),
                    "format": info.get("format"),
                    "ext": info.get("ext"),
                    "warning": "Ye URL IP-locked hai. Sirf server IP se kaam karega."
                }

        result = await loop.run_in_executor(None, _extract)
        increment_usage(user['api_key'], "/direct-url", video_id)
        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)}"}, status_code=500)


# =============================================
# ADMIN ENDPOINTS
# =============================================

async def admin_create_key(request: Request):
    """
    🔑 Nayi API key banao.
    Usage: /admin/create-key?client_name=Rahul+Bot&plan=paid&daily_limit=500&admin_key=YOUR_ADMIN_KEY
    """
    admin_error = verify_admin(request)
    if admin_error:
        return admin_error

    client_name = request.query_params.get("client_name")
    if not client_name:
        return JSONResponse({"error": "'client_name' parameter zaroori hai."}, status_code=400)

    plan = request.query_params.get("plan", "free")
    daily_limit = request.query_params.get("daily_limit")
    expires_days = request.query_params.get("expires_days")

    # Daily limit set karo
    if daily_limit:
        daily_limit = int(daily_limit)
    else:
        limit_map = {
            "free": FREE_PLAN_DAILY_LIMIT,
            "paid": PAID_PLAN_DAILY_LIMIT,
            "unlimited": UNLIMITED_PLAN_DAILY_LIMIT,
        }
        daily_limit = limit_map.get(plan, FREE_PLAN_DAILY_LIMIT)

    expires_in_days = int(expires_days) if expires_days else None

    result = create_user(
        client_name=client_name,
        plan_type=plan,
        daily_limit=daily_limit,
        expires_in_days=expires_in_days
    )

    return JSONResponse(result)


async def admin_revoke_key(request: Request):
    """
    🚫 API key band karo.
    Usage: /admin/revoke-key?api_key=MUS_xxxxx&admin_key=YOUR_ADMIN_KEY
    """
    admin_error = verify_admin(request)
    if admin_error:
        return admin_error

    api_key = request.query_params.get("api_key")
    if not api_key:
        return JSONResponse({"error": "'api_key' parameter zaroori hai."}, status_code=400)

    result = revoke_api_key(api_key)
    return JSONResponse(result)


async def admin_list_users(request: Request):
    """
    👥 Saare users dekho.
    Usage: /admin/users?admin_key=YOUR_ADMIN_KEY
    """
    admin_error = verify_admin(request)
    if admin_error:
        return admin_error

    users = get_all_users()
    return JSONResponse({"total_users": len(users), "users": users})


async def admin_stats_view(request: Request):
    """
    📊 API statistics.
    Usage: /admin/stats?admin_key=YOUR_ADMIN_KEY
    """
    admin_error = verify_admin(request)
    if admin_error:
        return admin_error

    stats = get_stats()
    stats["cache_size"] = cache.size
    return JSONResponse(stats)


async def admin_clear_cache(request: Request):
    """
    🧹 Cache saaf karo.
    Usage: /admin/clear-cache?admin_key=YOUR_ADMIN_KEY
    """
    admin_error = verify_admin(request)
    if admin_error:
        return admin_error

    old_size = cache.size
    cache.clear()
    return JSONResponse({"message": f"Cache cleared! {old_size} items removed."})


# =============================================
# APP STARTUP
# =============================================
def on_startup():
    init_database()
    print("=" * 50)
    print("🎵 Music Streaming API Started!")
    print(f"📁 Cookies: {'✅ Loaded' if COOKIES_FILE else '❌ Not found'}")
    print(f"🌐 Proxy: {'✅ ' + PROXY_URL if PROXY_URL else '❌ Not configured'}")
    print("=" * 50)


# =============================================
# ROUTES DEFINE KARO
# =============================================
app = Starlette(
    debug=False,
    on_startup=[on_startup],
    routes=[
        # Public
        Route("/", home),

        # Client endpoints (API key required)
        Route("/search", search_song),
        Route("/info/{video_id}", get_video_info),
        Route("/stream/{video_id}", stream_audio),
        Route("/direct-url/{video_id}", direct_url),

        # Admin endpoints (Admin key required)
        Route("/admin/create-key", admin_create_key, methods=["GET", "POST"]),
        Route("/admin/revoke-key", admin_revoke_key, methods=["GET", "POST"]),
        Route("/admin/users", admin_list_users),
        Route("/admin/stats", admin_stats_view),
        Route("/admin/clear-cache", admin_clear_cache, methods=["GET", "POST"]),
    ]
)
