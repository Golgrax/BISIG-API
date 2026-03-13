import os
import json
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from services import video_service

app = FastAPI(title="BISIG Sign Language API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEOS_DIR = "/workspaces/BISIG-API/videos"
if not os.path.exists(VIDEOS_DIR):
    os.makedirs(VIDEOS_DIR)

# Serve local video files
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")

@app.get("/translate")
async def translate_text(request: Request, text: str = Query(..., description="The text to translate")):
    """
    Translates text to a sequence of sign language video URLs.
    Detects public URL to handle proxies (GitHub Codespaces, etc).
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    video_results = await video_service.process_text(text)
    
    # Detect the actual public host and protocol
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    proto = request.headers.get("x-forwarded-proto", "http")
    base_url = f"{proto}://{host}"
    
    # Construct full URLs for the videos
    response_data = []
    for item in video_results:
        response_data.append({
            "word": item["word"],
            "url": f"{base_url}/videos/{item['filename']}",
            "type": item["type"]
        })
    
    return {
        "original_text": text,
        "videos": response_data
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
