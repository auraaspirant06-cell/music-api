"""
===============================================
  API TEST CLIENT (test_client.py)
===============================================
Ye script aapki Music API ko test karne ke liye hai.
Pehle API server start karein, phir ye script chalayein.

Usage:
  1. Ek terminal me: uvicorn main:app --host 0.0.0.0 --port 8000
  2. Doosre terminal me: python test_client.py
"""

import requests
import sys

# =============================================
# YAHA APNI SETTINGS BHAREIN
# =============================================
# Agar locally test kar rahe hain toh http://localhost:8000
# Agar VPS par hai toh http://YOUR_SERVER_IP:8000
API_BASE_URL = "http://localhost:8000"

# Admin key (config.py me jo set ki hai wahi daalein)
ADMIN_KEY = "fpO4PThOuoxcNTR3d-A3Rd0rb_unZibPCD2KltsYbDU"


def print_header(text):
    """Sundar header print karta hai."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_server_status():
    """Step 1: Server online hai ya nahi check karo."""
    print_header("TEST 1: Server Status Check")
    try:
        resp = requests.get(f"{API_BASE_URL}/")
        data = resp.json()
        print(f"✅ Server Status: {data['status']}")
        print(f"   API Name: {data['api_name']}")
        return True
    except requests.ConnectionError:
        print("❌ Server se connect nahi ho pa raha!")
        print("   Kya aapne server start kiya hai?")
        print("   Command: uvicorn main:app --host 0.0.0.0 --port 8000")
        return False


def test_create_api_key():
    """Step 2: Admin key se ek test client banao."""
    print_header("TEST 2: Create Test API Key (Admin)")
    
    resp = requests.post(
        f"{API_BASE_URL}/admin/create-key",
        params={
            "client_name": "Test Bot",
            "plan": "paid",
            "daily_limit": 100,
            "admin_key": ADMIN_KEY
        }
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ API Key Created!")
        print(f"   Client: {data['client_name']}")
        print(f"   Key: {data['api_key']}")
        print(f"   Plan: {data['plan_type']}")
        print(f"   Daily Limit: {data['daily_limit']}")
        return data['api_key']
    else:
        print(f"❌ Error: {resp.json()}")
        return None


def test_search(api_key):
    """Step 3: Gaana search karo."""
    print_header("TEST 3: Search Song")
    
    query = "Arijit Singh Tum Hi Ho"
    print(f"   Searching: '{query}'...")
    
    resp = requests.get(
        f"{API_BASE_URL}/search",
        params={"q": query, "api_key": api_key}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        result = data['results'][0]
        print(f"✅ Song Found!")
        print(f"   Title: {result['title']}")
        print(f"   Video ID: {result['id']}")
        print(f"   Duration: {result.get('duration_string', 'N/A')}")
        print(f"   Channel: {result['channel']}")
        print(f"   Source: {data['source']}")
        return result['id']
    else:
        print(f"❌ Error: {resp.json()}")
        return None


def test_stream(api_key, video_id):
    """Step 4: Audio stream test karo."""
    print_header("TEST 4: Audio Stream Test")
    
    print(f"   Streaming video: {video_id}...")
    
    resp = requests.get(
        f"{API_BASE_URL}/stream/{video_id}",
        params={"api_key": api_key},
        stream=True  # Streaming mode me download karo
    )
    
    if resp.status_code == 200:
        # Pehle 100KB download karke check karo ki audio aa raha hai
        total_bytes = 0
        for chunk in resp.iter_content(chunk_size=8192):
            total_bytes += len(chunk)
            if total_bytes > 102400:  # 100KB enough hai test ke liye
                break
        
        print(f"✅ Audio Stream Working!")
        print(f"   Downloaded: {total_bytes / 1024:.1f} KB (test sample)")
        print(f"   Content-Type: {resp.headers.get('content-type', 'unknown')}")
        
        # Full stream URL bhi show karo
        stream_url = f"{API_BASE_URL}/stream/{video_id}?api_key={api_key}"
        print(f"\n   🎵 Browser me audio sun'ne ke liye ye URL kholein:")
        print(f"   {stream_url}")
    else:
        print(f"❌ Stream Error: Status {resp.status_code}")
        try:
            print(f"   Detail: {resp.json()}")
        except Exception:
            print(f"   Response: {resp.text[:200]}")


def test_admin_stats():
    """Step 5: Admin stats dekho."""
    print_header("TEST 5: Admin Statistics")
    
    resp = requests.get(
        f"{API_BASE_URL}/admin/stats",
        params={"admin_key": ADMIN_KEY}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Stats Retrieved!")
        print(f"   Total Users: {data['total_users']}")
        print(f"   Active Users: {data['active_users']}")
        print(f"   Today's Requests: {data['total_requests_today']}")
        print(f"   All-Time Requests: {data['total_requests_all_time']}")
        print(f"   Cache Size: {data['cache_size']} items")
    else:
        print(f"❌ Error: {resp.json()}")


def test_invalid_key():
    """Step 6: Invalid key se access try karo (should fail)."""
    print_header("TEST 6: Invalid Key Test (Should Fail)")
    
    resp = requests.get(
        f"{API_BASE_URL}/search",
        params={"q": "test", "api_key": "FAKE_KEY_12345"}
    )
    
    if resp.status_code == 403:
        print(f"✅ Security Working! Invalid key correctly rejected.")
        print(f"   Response: {resp.json()['detail']}")
    else:
        print(f"⚠️ Unexpected status: {resp.status_code}")


# =============================================
# MAIN - Saare tests ek saath chalao
# =============================================
if __name__ == "__main__":
    print("\n🎵 MUSIC API TEST SUITE 🎵")
    print("Ye script aapki API ke saare endpoints test karegi.\n")
    
    # Test 1: Server check
    if not test_server_status():
        print("\n⛔ Server offline hai. Pehle server start karein.")
        sys.exit(1)
    
    # Test 2: API key banao
    test_key = test_create_api_key()
    if not test_key:
        print("\n⛔ API key nahi ban payi. Admin key check karein.")
        sys.exit(1)
    
    # Test 3: Search
    video_id = test_search(test_key)
    
    # Test 4: Stream
    if video_id:
        test_stream(test_key, video_id)
    
    # Test 5: Stats
    test_admin_stats()
    
    # Test 6: Security check
    test_invalid_key()
    
    print_header("ALL TESTS COMPLETED! 🎉")
    print("   Agar saare tests ✅ hain toh aapki API ready hai!")
    print("   Ab isko VPS par deploy karein (README.md padhein).")
    print()
