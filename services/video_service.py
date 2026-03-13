import httpx
import os
import json
import asyncio
import aiofiles

# Load config
CONFIG_PATH = "/workspaces/BISIG-API/config.json"
CACHE_PATH = "/workspaces/BISIG-API/cache.json"
VIDEOS_DIR = "/workspaces/BISIG-API/videos"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    S3_BASE_URL = config.get("s3_base_url", "https://pocketsign.s3-us-west-2.amazonaws.com/")
else:
    S3_BASE_URL = "https://pocketsign.s3-us-west-2.amazonaws.com/"

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

_cache = load_cache()

async def get_or_fetch_video(word: str, is_letter: bool = False):
    word = word.lower().strip()
    if not word or not word.isalnum():
        return None

    filename = f"{word}.mp4"
    local_path = os.path.join(VIDEOS_DIR, filename)

    # 1. Check if we already have it locally
    if os.path.exists(local_path):
        return {"word": word, "filename": filename, "type": "letter" if is_letter else "word"}

    # 2. Check cache to see if we've already marked it as non-existent
    if word in _cache and _cache[word] is None:
        return None

    # 3. Fetch from S3 and save locally
    url = f"{S3_BASE_URL}{filename}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, follow_redirects=True)
            if response.status_code == 200:
                async with aiofiles.open(local_path, mode='wb') as f:
                    await f.write(response.content)
                
                # Update JSON cache with filename
                _cache[word] = filename
                save_cache(_cache)
                return {"word": word, "filename": filename, "type": "letter" if is_letter else "word"}
            else:
                # Mark as non-existent
                _cache[word] = None
                save_cache(_cache)
                return None
        except Exception as e:
            print(f"Error fetching {word}: {e}")
            return None

async def process_text(text: str):
    words = text.replace('+', ' ').split()
    results = []

    for word in words:
        video = await get_or_fetch_video(word)
        if video:
            results.append(video)
        else:
            for char in word:
                char_video = await get_or_fetch_video(char, is_letter=True)
                if char_video:
                    results.append(char_video)
    
    return results
