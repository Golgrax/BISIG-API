import cv2
import mediapipe as mp
import json
import os
import numpy as np
import math
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Paths to model files relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
POSE_MODEL_PATH = os.path.join(MODELS_DIR, "pose_landmarker.task")
HAND_MODEL_PATH = os.path.join(MODELS_DIR, "hand_landmarker.task")
FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")

# Skeleton connection definitions
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Torso & Arms
    (11, 23), (12, 24), (23, 24), # Hips
    (23, 25), (24, 26), (25, 27), (26, 28) # Legs
]

# Specific hand colors for fingers
FINGER_COLORS = [
    ((255, 255, 0), [(0, 1), (1, 2), (2, 3), (3, 4)]),     # Thumb: Yellow
    ((0, 255, 255), [(5, 6), (6, 7), (7, 8), (0, 5)]),     # Index: Cyan
    ((255, 0, 255), [(9, 10), (10, 11), (11, 12), (5, 9)]),# Middle: Magenta
    ((0, 255, 0), [(13, 14), (14, 15), (15, 16), (9, 13)]),# Ring: Green
    ((200, 200, 200), [(17, 18), (18, 19), (19, 20), (13, 17), (0, 17)]) # Pinky/Palm: White
]

# Face contours for expressions (MediaPipe FaceMesh indices)
FACE_CONTOURS = [
    # Lips
    (61, 146), (146, 91), (91, 181), (181, 84), (84, 17), (17, 314), (314, 405), (405, 321), (321, 375), (375, 291),
    (61, 185), (185, 40), (40, 39), (39, 37), (37, 0), (0, 267), (267, 269), (269, 270), (270, 409), (409, 291),
    # Left Eye
    (33, 7), (7, 163), (163, 144), (144, 145), (145, 153), (153, 154), (154, 155), (155, 133),
    (33, 246), (246, 161), (161, 160), (160, 159), (159, 158), (158, 157), (157, 173), (173, 133),
    # Right Eye
    (263, 249), (249, 390), (390, 373), (373, 374), (374, 380), (380, 381), (381, 382), (382, 362),
    (263, 466), (466, 388), (388, 387), (387, 386), (386, 385), (385, 384), (384, 398), (398, 362),
    # Eyebrows
    (70, 63), (63, 105), (105, 66), (66, 107), (107, 55),
    (300, 293), (293, 334), (334, 296), (296, 336), (334, 285)
]

def interpolate_frames(frame_a, frame_b, num_frames=15):
    """
    Creates num_frames interpolated frames between frame_a and frame_b.
    Now includes face interpolation and wrist-anchoring for hands.
    """
    interpolated = []
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    for i in range(1, num_frames + 1):
        alpha = i / (num_frames + 1)
        new_frame = {"pose": None, "left_hand": None, "right_hand": None, "face": None}
        
        for key in ["pose", "left_hand", "right_hand", "face"]:
            lms_a = frame_a.get(key)
            lms_b = frame_b.get(key)
            
            # Anchor missing hands to wrists
            if key in ["left_hand", "right_hand"]:
                wrist_idx = LEFT_WRIST if key == "left_hand" else RIGHT_WRIST
                if not lms_a and lms_b and frame_a.get("pose"):
                    wrist = frame_a["pose"][wrist_idx]
                    lms_a = [{"x": wrist["x"], "y": wrist["y"], "z": wrist["z"]} for _ in range(21)]
                elif not lms_b and lms_a and frame_b.get("pose"):
                    wrist = frame_b["pose"][wrist_idx]
                    lms_b = [{"x": wrist["x"], "y": wrist["y"], "z": wrist["z"]} for _ in range(21)]

            if lms_a and lms_b and len(lms_a) == len(lms_b):
                new_lms = []
                for la, lb in zip(lms_a, lms_b):
                    interp_lm = {
                        "x": la["x"] * (1 - alpha) + lb["x"] * alpha,
                        "y": la["y"] * (1 - alpha) + lb["y"] * alpha,
                        "z": la["z"] * (1 - alpha) + lb["z"] * alpha
                    }
                    if "visibility" in la and "visibility" in lb:
                        interp_lm["visibility"] = la["visibility"] * (1 - alpha) + lb["visibility"] * alpha
                    new_lms.append(interp_lm)
                new_frame[key] = new_lms
            elif lms_a: new_frame[key] = lms_a
            elif lms_b: new_frame[key] = lms_b
        interpolated.append(new_frame)
    return interpolated

async def extract_skeleton(video_path: str):
    """
    Extracts skeleton keypoints (pose, hands, face) from a video file using MediaPipe Tasks.
    """
    if not os.path.exists(video_path): return None

    base_options = lambda p: python.BaseOptions(model_asset_path=p)
    opt_pose = vision.PoseLandmarkerOptions(base_options=base_options(POSE_MODEL_PATH), running_mode=vision.RunningMode.VIDEO)
    opt_hand = vision.HandLandmarkerOptions(base_options=base_options(HAND_MODEL_PATH), running_mode=vision.RunningMode.VIDEO, num_hands=2, min_hand_detection_confidence=0.6)
    opt_face = vision.FaceLandmarkerOptions(base_options=base_options(FACE_MODEL_PATH), running_mode=vision.RunningMode.VIDEO)

    results_data = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    with vision.PoseLandmarker.create_from_options(opt_pose) as pose_l, \
         vision.HandLandmarker.create_from_options(opt_hand) as hand_l, \
         vision.FaceLandmarker.create_from_options(opt_face) as face_l:
        
        f_idx = 0
        while cap.isOpened():
            success, frame = cap.read()
            if not success: break

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            ts_ms = int((f_idx / fps) * 1000)
            
            p_res = pose_l.detect_for_video(mp_image, ts_ms)
            h_res = hand_l.detect_for_video(mp_image, ts_ms)
            f_res = face_l.detect_for_video(mp_image, ts_ms)

            f_lms = {"pose": None, "left_hand": None, "right_hand": None, "face": None}

            if p_res.pose_landmarks:
                f_lms["pose"] = [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} for lm in p_res.pose_landmarks[0]]
            
            if f_res.face_landmarks:
                f_lms["face"] = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in f_res.face_landmarks[0]]

            if h_res.hand_landmarks and f_lms["pose"]:
                p_lms = f_lms["pose"]
                lw, rw = (p_lms[15]["x"], p_lms[15]["y"]), (p_lms[16]["x"], p_lms[16]["y"])
                for i, h_pts in enumerate(h_res.hand_landmarks):
                    h_root = (h_pts[0].x, h_pts[0].y)
                    dist_l = math.sqrt((h_root[0]-lw[0])**2 + (h_root[1]-lw[1])**2)
                    dist_r = math.sqrt((h_root[0]-rw[0])**2 + (h_root[1]-rw[1])**2)
                    key = "left_hand" if dist_l < dist_r else "right_hand"
                    f_lms[key] = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in h_pts]
            
            results_data.append(f_lms)
            f_idx += 1

    cap.release()
    return results_data

def render_skeleton_video(skeleton_data, output_path, width=640, height=480, fps=30):
    """
    Renders the high-fidelity skeleton with face expressions and multi-color fingers.
    """
    width, height = (width // 2) * 2, (height // 2) * 2
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'MJPG'), fps, (width, height))
    if not out.isOpened(): return

    for frame in skeleton_data:
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # 1. Draw Face (Gray/White) - Shows expressions
        if frame.get("face"):
            lms = frame["face"]
            for s_idx, e_idx in FACE_CONTOURS:
                if s_idx < len(lms) and e_idx < len(lms):
                    p1 = (int(lms[s_idx]["x"] * width), int(lms[s_idx]["y"] * height))
                    p2 = (int(lms[e_idx]["x"] * width), int(lms[e_idx]["y"] * height))
                    cv2.line(img, p1, p2, (180, 180, 180), 1)

        # 2. Draw Pose (Vibrant Green)
        if frame.get("pose"):
            lms = frame["pose"]
            for s_idx, e_idx in POSE_CONNECTIONS:
                if s_idx < len(lms) and e_idx < len(lms):
                    s, e = lms[s_idx], lms[e_idx]
                    if s.get("visibility", 1.0) > 0.5 and e.get("visibility", 1.0) > 0.5:
                        p1, p2 = (int(s["x"]*width), int(s["y"]*height)), (int(e["x"]*width), int(e["y"]*height))
                        cv2.line(img, p1, p2, (0, 255, 100), 3)
            for lm in lms:
                if lm.get("visibility", 1.0) > 0.5:
                    cv2.circle(img, (int(lm["x"]*width), int(lm["y"]*height)), 4, (0, 255, 0), -1)

        # 3. Draw Hands (Multi-Color Fingers for readability)
        for key in ["left_hand", "right_hand"]:
            if frame.get(key):
                lms = frame[key]
                for color, conns in FINGER_COLORS:
                    for s_idx, e_idx in conns:
                        p1, p2 = (int(lms[s_idx]["x"]*width), int(lms[s_idx]["y"]*height)), (int(lms[e_idx]["x"]*width), int(lms[e_idx]["y"]*height))
                        cv2.line(img, p1, p2, color, 2)
                for lm in lms:
                    cv2.circle(img, (int(lm["x"]*width), int(lm["y"]*height)), 3, (255, 255, 255), -1)

        out.write(img)
    out.release()

def save_skeleton_data(data, output_path):
    with open(output_path, 'w') as f: json.dump(data, f)
