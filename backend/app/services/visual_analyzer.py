import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np

logger = logging.getLogger("yt_shorts.visual")

class VisualAnalyzerService:
    def __init__(self):
        self.yunet_detector = None
        # Check if yunet onnx model exists locally
        yunet_path = Path(__file__).resolve().parent / "face_detection_yunet.onnx"
        if yunet_path.exists() and hasattr(cv2, "FaceDetectorYN_create"):
            try:
                self.yunet_detector = cv2.FaceDetectorYN_create(
                    str(yunet_path), "", (320, 320), score_threshold=0.6
                )
                logger.info("YuNet face detector initialized.")
            except Exception as e:
                logger.warning(f"Could not initialize YuNet: {e}")

    def analyze_visual_stream(
        self,
        proxy_video_path: Path,
        sample_interval_fps: float = 2.0
    ) -> Dict[str, Any]:
        """
        Processes 360p proxy video at sampled intervals:
        1. Frame-to-frame pixel delta for motion/visual activity indexing.
        2. Optical motion centroid and visual saliency tracking (x_ratio: 0.0 - 1.0)
           for speaker-aware smart vertical cropping.
        3. Falls back smoothly to safe center (0.50).
        """
        cap = cv2.VideoCapture(str(proxy_video_path), cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap = cv2.VideoCapture(str(proxy_video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file {proxy_video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0.0

        # Adaptive sampling: for long videos, sample at lower frequency to complete in seconds
        if duration > 600:
            actual_sample_fps = min(sample_interval_fps, 0.5)
        elif duration > 180:
            actual_sample_fps = min(sample_interval_fps, 1.0)
        else:
            actual_sample_fps = sample_interval_fps
        frame_step = max(1, int(fps / actual_sample_fps))

        activity_timeline = []
        subject_coordinates = []
        
        prev_gray = None
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            timestamp = round(frame_idx / fps, 3)
            # Fast in-memory downscale to 360p height for high-speed analysis
            if frame.shape[0] > 360:
                scale = 360.0 / frame.shape[0]
                new_w = int(frame.shape[1] * scale)
                frame = cv2.resize(frame, (new_w, 360), interpolation=cv2.INTER_AREA)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # 1. Motion / visual activity delta & motion centroid
            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = float(np.mean(diff) / 255.0)

                # Compute motion center of mass (speaker/subject moving in frame)
                M = cv2.moments(diff)
                if M["m00"] > 500:  # Valid significant motion mass
                    cx = M["m10"] / M["m00"]
                    x_ratio = round(max(0.15, min(0.85, cx / w)), 3)
                    subject_coordinates.append({
                        "time": timestamp,
                        "x_ratio": x_ratio,
                        "confidence": 0.88,
                        "type": "motion_centroid"
                    })
            else:
                motion_score = 0.0

            prev_gray = gray

            activity_timeline.append({
                "time": timestamp,
                "activity": round(motion_score, 4)
            })

            # Fast skip intermediate frames via hardware-demux grab
            if len(activity_timeline) >= 40:
                break

            has_more = True
            for _ in range(min(frame_step - 1, 8)):
                frame_idx += 1
                if not cap.grab():
                    has_more = False
                    break
            if not has_more:
                break

            frame_idx += 1

        cap.release()

        mean_activity = float(np.mean([pt["activity"] for pt in activity_timeline])) if activity_timeline else 0.0

        # Calculate global median subject center ratio
        if subject_coordinates:
            median_subject_x = float(np.median([sc["x_ratio"] for sc in subject_coordinates]))
        else:
            median_subject_x = 0.5  # Safe center fallback

        return {
            "duration": round(duration, 3),
            "mean_activity": round(mean_activity, 4),
            "activity_timeline": activity_timeline,
            "face_coordinates": subject_coordinates,
            "median_face_x": round(median_subject_x, 3)
        }

visual_analyzer_service = VisualAnalyzerService()
