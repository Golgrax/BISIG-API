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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
SKELETON_VIDEOS_DIR = os.path.join(BASE_DIR, "skeleton_videos")

# Serve local video files
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
app.mount("/skeleton_videos", StaticFiles(directory=SKELETON_VIDEOS_DIR), name="skeleton_videos")

@app.get("/translate")
async def translate_text(
    request: Request, 
    text: str = Query(..., description="The text to translate"),
    format: str = Query("video", description="Output format: 'video', 'skeleton', 'skeleton_video', or 'full_skeleton_video'")
):
    """
    Translates text to a sequence of sign language video URLs or skeleton data/videos.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Handle full sequence combined video separately
    if format == "full_skeleton_video":
        filename = await video_service.get_full_skeleton_video_for_text(text)
        if not filename:
             raise HTTPException(status_code=404, detail="Could not generate combined skeleton video")
        
        host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
        proto = request.headers.get("x-forwarded-proto", "http")
        base_url = f"{proto}://{host}"
        
        return {
            "original_text": text,
            "format": format,
            "url": f"{base_url}/skeleton_videos/{filename}"
        }

    include_skeleton = (format == "skeleton")
    include_skeleton_video = (format == "skeleton_video")
    
    video_results = await video_service.process_text(
        text, 
        include_skeleton=include_skeleton,
        include_skeleton_video=include_skeleton_video
    )
    
    # Detect the actual public host and protocol
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    proto = request.headers.get("x-forwarded-proto", "http")
    base_url = f"{proto}://{host}"
    
    # Construct response data
    response_data = []
    for item in video_results:
        result_item = {
            "word": item["word"],
            "type": item["type"]
        }
        
        if format == "skeleton":
            result_item["skeleton"] = item.get("skeleton")
        elif format == "skeleton_video":
            video_filename = item.get("skeleton_video")
            result_item["url"] = f"{base_url}/skeleton_videos/{video_filename}" if video_filename else None
        else:
            result_item["url"] = f"{base_url}/videos/{item['filename']}"
            
        response_data.append(result_item)
    
    return {
        "original_text": text,
        "format": format,
        "results": response_data
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
