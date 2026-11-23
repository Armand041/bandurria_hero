import cv2
import mediapipe as mp
import numpy as np
from config import config


class HandTracker:
    def __init__(self) -> None:
        base_options = mp.tasks.BaseOptions(model_asset_path=config.model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=config.num_hands,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.connections = mp.solutions.hands.HAND_CONNECTIONS

    def detect(self, frame_bgr, timestamp_ms):
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def check_hit(self, detection_result, target_px, frame_shape, scale) -> bool:
        if not detection_result or not detection_result.hand_landmarks:
            return False

        h, w = frame_shape[:2]
        target_norm = (target_px[0] / w, target_px[1] / h)
        threshold = config.hit_threshold * scale

        for hand_landmarks in detection_result.hand_landmarks:
            for idx in config.fingertip_indices:
                lm = hand_landmarks[idx]
                if self._calculate_distance((lm.x, lm.y), target_norm) < threshold:
                    return True

        return False

    @staticmethod
    def _calculate_distance(point1, point2) -> float:
        return float(np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2))

    def close(self):
        self.landmarker.close()
