import httpx
import os
import json
import asyncio
import aiofiles
import re
import hashlib
from services import skeleton_service

# Load config relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CACHE_PATH = os.path.join(BASE_DIR, "cache.json")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
SKELETONS_DIR = os.path.join(BASE_DIR, "skeletons")
SKELETON_VIDEOS_DIR = os.path.join(BASE_DIR, "skeleton_videos")

for d in [VIDEOS_DIR, SKELETONS_DIR, SKELETON_VIDEOS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

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
                
                _cache[word] = filename
                save_cache(_cache)
                return {"word": word, "filename": filename, "type": "letter" if is_letter else "word"}
            else:
                _cache[word] = None
                save_cache(_cache)
                return None
        except Exception as e:
            print(f"Error fetching {word}: {e}")
            return None

async def get_skeleton_for_video(video_info: dict):
    if not video_info:
        return None
    
    word = video_info["word"]
    filename = video_info["filename"]
    video_path = os.path.join(VIDEOS_DIR, filename)
    skeleton_filename = f"{word}.json"
    skeleton_path = os.path.join(SKELETONS_DIR, skeleton_filename)

    if os.path.exists(skeleton_path):
        async with aiofiles.open(skeleton_path, mode='r') as f:
            return json.loads(await f.read())

    skeleton_data = await skeleton_service.extract_skeleton(video_path)
    if skeleton_data:
        async with aiofiles.open(skeleton_path, mode='w') as f:
            await f.write(json.dumps(skeleton_data))
    
    return skeleton_data

async def get_skeleton_video_for_word(video_info: dict):
    if not video_info:
        return None
    
    word = video_info["word"]
    skeleton_video_filename = f"{word}_skeleton.avi"
    skeleton_video_path = os.path.join(SKELETON_VIDEOS_DIR, skeleton_video_filename)

    if os.path.exists(skeleton_video_path):
        return skeleton_video_filename

    skeleton_data = await get_skeleton_for_video(video_info)
    if not skeleton_data:
        return None
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, skeleton_service.render_skeleton_video, skeleton_data, skeleton_video_path)
    
    return skeleton_video_filename

async def get_full_skeleton_video_for_text(text: str):
    """
    Generates a single combined skeleton video for a whole text phrase with smooth transitions.
    """
    text_hash = hashlib.sha256(text.lower().strip().encode()).hexdigest()[:16]
    combined_video_filename = f"combined_{text_hash}.avi"
    combined_video_path = os.path.join(SKELETON_VIDEOS_DIR, combined_video_filename)

    if os.path.exists(combined_video_path):
        return combined_video_filename

    # Get all individual word results
    video_results = await process_text(text, include_skeleton=True)
    if not video_results:
        return None

    all_frames = []
    for i, result in enumerate(video_results):
        current_skeleton = result.get("skeleton")
        if not current_skeleton:
            continue
        
        # If this is not the first word, interpolate from the last word's end to this word's start
        if all_frames and current_skeleton:
            last_frame = all_frames[-1]
            first_frame_new = current_skeleton[0]
            interpolation = skeleton_service.interpolate_frames(last_frame, first_frame_new, num_frames=10)
            all_frames.extend(interpolation)
        
        all_frames.extend(current_skeleton)

    if not all_frames:
        return None

    # Render the combined video
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, skeleton_service.render_skeleton_video, all_frames, combined_video_path)
    
    return combined_video_filename

async def process_text(text: str, include_skeleton: bool = False, include_skeleton_video: bool = False):
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    words = clean_text.split()
    results = []

    for word in words:
        video = await get_or_fetch_video(word)
        if video:
            if include_skeleton:
                video["skeleton"] = await get_skeleton_for_video(video)
            if include_skeleton_video:
                video["skeleton_video"] = await get_skeleton_video_for_word(video)
            results.append(video)
        else:
            for char in word:
                if char.isalnum():
                    char_video = await get_or_fetch_video(char, is_letter=True)
                    if char_video:
                        if include_skeleton:
                            char_video["skeleton"] = await get_skeleton_for_video(char_video)
                        if include_skeleton_video:
                            char_video["skeleton_video"] = await get_skeleton_video_for_word(char_video)
                        results.append(char_video)
    
    return results
