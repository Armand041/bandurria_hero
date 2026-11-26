"""
Módulo de visión por computador encargado de detectar los landmarks de la mano
mediante MediaPipe y evaluar si el usuario acierta las notas pisadas o al aire.
"""

import cv2
import mediapipe as mp
import numpy as np
from config import config


class HandTracker:
    def __init__(self) -> None:
        """Carga el modelo Hand Landmarker de MediaPipe en modo vídeo."""
        base_options = mp.tasks.BaseOptions(model_asset_path=config.model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=config.num_hands,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.connections = mp.solutions.hands.HAND_CONNECTIONS

    def detect(self, frame_bgr, timestamp_ms):
        """Convierte el fotograma de OpenCV a RGB y ejecuta la detección de mano."""
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def check_hit(self, detection_result, target_px, frame_shape, scale) -> bool:
        """Comprueba si alguna yema de los dedos cae cerca de la nota objetivo."""
        if not detection_result or not detection_result.hand_landmarks:
            return False

        h, w = frame_shape[:2]
        target_norm = (target_px[0] / w, target_px[1] / h)
        threshold = config.hit_threshold * scale # El margen se adapta al zoom del diapasón

        for hand_landmarks in detection_result.hand_landmarks:
            for idx in config.fingertip_indices:
                lm = hand_landmarks[idx]
                if self._calculate_distance((lm.x, lm.y), target_norm) < threshold:
                    return True

        return False

    def check_open_hit(self, detection_result, target_px, fretboard_rect, frame_shape, scale) -> bool:
        """Acierto al aire: la mano está visible pero ningún dedo pisa el diapasón."""
        if not detection_result or not detection_result.hand_landmarks:
            return False

        cur_x, _, cur_w, _ = fretboard_rect[:4]
        h, w = frame_shape[:2]
        string_y = target_px[1]

        y_tolerance = max(8, int(10 * scale))

        for hand_landmarks in detection_result.hand_landmarks:
            for idx in config.fingertip_indices:
                lm = hand_landmarks[idx]
                px, py = lm.x * w, lm.y * h
                # Si algún dedo está dentro del área de trastes, no está tocando al aire
                if cur_x <= px <= cur_x + cur_w and abs(py - string_y) < y_tolerance:
                    return False

        return True

    @staticmethod
    def _calculate_distance(point1, point2) -> float:
        """Calcula la distancia euclídea entre dos puntos normalizados."""
        return float(np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2))

    def close(self):
        self.landmarker.close()
