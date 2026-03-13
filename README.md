# BISIG Sign Language API

A high-performance REST API designed to translate text into sign language video sequences and high-fidelity skeleton datasets.

## 🚀 Features

- **Text-to-Video Translation**: Translates text phrases into a sequence of `.mp4` video URLs.
- **Full Sequence Skeleton Rendering**: Use `format=full_skeleton_video` to get a single, continuous video of the entire phrase with smooth transitions.
- **Pose Interpolation**: Automatically calculates "bridge" frames between words to prevent teleporting hands and ensure fluid movement.
- **High-Fidelity Tracking**: 
    - **Face Expressions**: Tracks lips, eyes, and eyebrows to capture the non-verbal nuances of sign language.
    - **Color-Coded Fingers**: Each finger is uniquely colored (Yellow, Cyan, Magenta, Green, White) for maximum clarity in finger-spelling.
    - **Hand Stabilization**: Advanced spatial verification to fix AI handedness-swap glitches.
- **Skeleton Dataset Extraction**: Use `format=skeleton` to get raw 3D landmark coordinates for AI training and motion analysis.
- **Smart Fallback**: Automatically falls back to letter-by-letter spelling if a specific word video is missing.
- **Auto-Download & Local Caching**: Videos and AI-generated skeletons are cached locally for near-instant subsequent requests.
- **Proxy-Aware URLs**: Automatically detects public hosts (e.g., GitHub Codespaces) for valid media playback.

## 🛠️ API Endpoints

### `GET /translate?text=...&format=...`
Translates text into a sequence of video URLs or skeleton datasets.

- **Parameters**:
  - `text`: (Required) The phrase to translate.
  - `format`: 
    - `video` (Default): Returns a list of original human sign language URLs.
    - `skeleton`: Returns raw JSON coordinates (Pose, Hands, Face) for every frame.
    - `skeleton_video`: Returns a rendered stick-figure video for each individual word.
    - `full_skeleton_video`: Returns one single combined video for the entire phrase with smooth transitions.

- **Example (Full Sequence)**: `/translate?text=hello+world&format=full_skeleton_video`

## 📁 Project Structure

- `main.py`: FastAPI application and endpoint logic.
- `services/video_service.py`: Core logic for caching and sequence combination.
- `services/skeleton_service.py`: AI logic for 3D keypoint extraction, interpolation, and rendering.
- `videos/`: Local storage for source `.mp4` files.
- `skeletons/`: Cache for extracted 3D landmark JSON data.
- `skeleton_videos/`: Cache for rendered stick-figure videos (`.avi`).
- `models/`: Storage for MediaPipe AI model files (`pose`, `hand`, `face`).

## ⚡ Setup & Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the server**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 🎨 Skeleton Color Guide
- **Body**: Vibrant Neon Green
- **Face**: Soft Gray (Contour mapping)
- **Thumb**: Yellow
- **Index**: Cyan
- **Middle**: Magenta
- **Ring**: Green
- **Pinky**: White
