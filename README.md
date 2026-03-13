# BISIG Sign Language API

A high-performance REST API designed to translate text into sign language video sequences.

## 🚀 Features

- **Text-to-Video Translation**: Translates text phrases into a sequence of `.mp4` video URLs.
- **Smart Fallback**: If a video for a specific word doesn't exist, the API automatically falls back to letter-by-letter spelling.
- **Auto-Download & Local Caching**: Videos are automatically fetched from an external S3 bucket, saved to local storage (`/videos`), and served locally for faster future access and offline reliability.
- **JSON Metadata**: Uses a simple, human-readable `cache.json` for persistence.
- **CORS Support**: Ready for integration with any web frontend.
- **Proxy-Aware URLs**: Automatically detects the public host (e.g., GitHub Codespaces) to provide valid, playable URLs.

## 🛠️ API Endpoints

### `GET /translate?text=...`
Translates text into a sequence of video URLs.
- **Example**: `/translate?text=hello+world`
- **Response**:
```json
{
  "original_text": "hello world",
  "videos": [
    { "word": "hello", "url": "https://.../videos/hello.mp4", "type": "word" },
    { "word": "w", "url": "https://.../videos/w.mp4", "type": "letter" },
    ...
  ]
}
```

### `GET /health`
Returns the status of the API.

## 📁 Project Structure

- `main.py`: FastAPI application and endpoint logic.
- `services/video_service.py`: Core logic for fetching, downloading, and caching.
- `videos/`: Local storage for downloaded `.mp4` files (ignored by git).
- `cache.json`: Persistence for word existence status (ignored by git).
- `config.json`: Configuration settings (S3 URL, local paths).

## ⚡ Setup & Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
