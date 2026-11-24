import numpy as np
import cv2
from config import config


class GameRenderer:
    def __init__(self, frame_w, frame_h) -> None:
        self.img_png_raw = cv2.imread(config.fretboard_img_path, cv2.IMREAD_UNCHANGED)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.speed = 1.0

        back = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        self.color_normal = np.full_like(back, config.color_normal)
        self.color_hit = np.full_like(back, config.color_hit)

    def adjust_zoom(self, delta):
        self.scale = float(np.clip(round(self.scale + delta, 2), config.min_scale, config.max_scale))

    def adjust_speed(self, n_speed):
        self.speed = round(n_speed, 2)

    def move_fretboard(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy

    def reset_transform(self):
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def _compute_fretboard_rect(self, frame_w, frame_h):
        base_w, base_h = config.fretboard_base_w, config.fretboard_base_h
        base_x, base_y = config.fretboard_base_x, config.fretboard_base_y

        cur_w = min(frame_w - 2, int(base_w * self.scale))
        cur_h = min(frame_h - 2, int(base_h * self.scale))

        ideal_x = base_x - (cur_w - base_w) / 2
        ideal_y = base_y - (cur_h - base_h) / 2

        cur_x = int(np.clip(ideal_x + self.offset_x, 0, max(0, frame_w - cur_w)))
        cur_y = int(np.clip(ideal_y + self.offset_y, 0, max(0, frame_h - cur_h)))

        actual_dx = cur_x - int(ideal_x)
        actual_dy = cur_y - int(ideal_y)

        return cur_x, cur_y, cur_w, cur_h, actual_dx, actual_dy

    def get_scaled_note_position(self, raw_pos, frame_w, frame_h):
        _, _, _, _, actual_dx, actual_dy = self._compute_fretboard_rect(frame_w, frame_h)
        center_x = config.fretboard_base_x + config.fretboard_base_w / 2
        center_y = config.fretboard_base_y + config.fretboard_base_h / 2

        return (
            int(center_x + (raw_pos[0] - center_x) * self.scale + actual_dx),
            int(center_y + (raw_pos[1] - center_y) * self.scale + actual_dy),
        )

    def draw_menu(self, frame, songs):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        cur_x, cur_y, cur_w, cur_h, _, _ = self._compute_fretboard_rect(w, h)
        preview_png = cv2.resize(self.img_png_raw, (cur_w, cur_h))
        frame = self._overlay_png(frame, preview_png, x=cur_x, y=cur_y)

        cv2.putText(frame, "BANDURRIA HERO", (160, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 255), 3)
        for idx, song in enumerate(songs, start=1):
            y_pos = 110 + (idx - 1) * 40
            cv2.putText(
                frame,
                f"{idx}. {song.name} (Tempo: {song.tempo})",
                (100, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
            )

        cv2.putText(
            frame,
            f"Velocidad [Z/X]: {self.speed}x",
            (100, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 200, 0),
            2,
        )

        cv2.putText(
            frame,
            f"Diapason [+/-] Zoom: {int(self.scale * 100)}% | [WASD] Mover | [R] Reset",
            (55, h - 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            "Pulsa 1, 2 o 3 para jugar (ESC para salir)",
            (95, h - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )
        return frame

    def draw_gameplay(self, frame, circle_layer, scaled_pos, note_hit, progress, score, remaining_time, wait_time=0.0, note_type=None, is_open=False):
        h, w = frame.shape[:2]
        cur_x, cur_y, cur_w, cur_h, _, _ = self._compute_fretboard_rect(w, h)
        img_png = cv2.resize(self.img_png_raw, (cur_w, cur_h))

        frame = self._overlay_png(frame, img_png, x=cur_x, y=cur_y)

        if circle_layer is not None and scaled_pos is not None:
            if progress is not None:
                radius = int((14 + 28 * (1.0 - progress)) * self.scale)
                cv2.circle(frame, scaled_pos, radius, (255, 255, 255), 2)

            if is_open:
                frame = self._draw_open_string_indicator(frame, scaled_pos, cur_x, cur_w, note_hit)
            else:
                frame = self._draw_vector_note(frame, scaled_pos, note_type or "negra")

        # Solo dibujar el círculo objetivo si ya hemos llegado a la primera nota
        if circle_layer is not None and scaled_pos is not None:
            frame = self._draw_vector_note(frame, scaled_pos, note_type)
            circle_layer[:] = 0
            cv2.circle(circle_layer, scaled_pos, max(4, int(10 * self.scale)), (255, 255, 255), -1)
            color_actual = self.color_hit if note_hit else self.color_normal
            frame = np.where(circle_layer != 0, color_actual, frame)

        if circle_layer is not None and scaled_pos is not None and progress is not None:
            radius = int((10 + 30 * (1.0 - progress)) * self.scale)
            cv2.circle(frame, scaled_pos, radius, (255, 255, 255), 2)
        elif wait_time > 0:
            cv2.putText(
                frame,
                f"Preparate: {wait_time:.1f}s",
                (w // 2 - 120, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 255),
                2,
            )

        cv2.putText(
            frame,
            f"Time: {remaining_time:.2f} - Points: {score}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        return frame

    def draw_hand_landmarks(self, frame, detection_result, connections):
        if not detection_result or not detection_result.hand_landmarks:
            return

        h, w = frame.shape[:2]
        for hand_landmarks in detection_result.hand_landmarks:
            for start_idx, end_idx in connections:
                start = hand_landmarks[start_idx]
                end = hand_landmarks[end_idx]
                cv2.line(
                    frame,
                    (int(start.x * w), int(start.y * h)),
                    (int(end.x * w), int(end.y * h)),
                    (255, 0, 0),
                    2,
                )

            for landmark in hand_landmarks:
                cv2.circle(frame, (int(landmark.x * w), int(landmark.y * h)), 3, (0, 255, 0), -1)

    def draw_game_over(self, frame_shape, song_name, score, total_notes, score_saved, player_name, top_scores):
        h, w = frame_shape[:2]
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        accuracy = (score / total_notes) * 100

        cv2.putText(frame, f"Score: {score} / {total_notes}", (150, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Accuracy: {accuracy:.1f}%", (150, 115), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if not score_saved:
            display_name = " ".join(player_name.ljust(3, "_"))
            cv2.putText(frame, "INTRODUCE TUS INICIALES:", (130, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, display_name, (230, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 255), 3)
            cv2.putText(frame, "Pulsa ENTER para guardar", (140, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        else:
            cv2.putText(frame, f"TOP 3 - {song_name} ({self.speed}x)", (150, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            for i, entry in enumerate(top_scores):
                texto = f"{i + 1}. {entry['name']} - {entry['score']}/{entry['total']} ({entry['accuracy']}%)"
                cv2.putText(frame, texto, (140, 225 + i * 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

            cv2.putText(frame, "Pulsa ENTER para volver al menu", (100, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "Pulsa ESC para salir", (150, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 128, 255), 2)

        return frame

    def _draw_vector_note(self, frame, scaled_pos, note_type):
        cx = scaled_pos[0]
        cy = max(30, scaled_pos[1] - int(28 * self.scale))
        r = max(4, int(6 * self.scale))
        stem_h = max(14, int(22 * self.scale))
        color = (255, 255, 255)

        # Cabeza de la nota (hueca para redonda/blanca, rellena para negra/corchea/semicorchea)
        filled = -1 if any(k in note_type for k in ("negra", "corchea", "semicorchea")) else 2
        cv2.ellipse(frame, (cx, cy), (r + 2, r), -20, 0, 360, color, filled)

        # Plica (palo vertical) para todas excepto la redonda
        if "redonda" not in note_type:
            stem_x = cx + r + 1
            cv2.line(frame, (stem_x, cy), (stem_x, cy - stem_h), color, 2)

            # Corchetes (banderines)
            if "corchea" in note_type:
                cv2.line(frame, (stem_x, cy - stem_h), (stem_x + 8, cy - stem_h + 7), color, 2)
            if "semicorchea" in note_type:
                cv2.line(frame, (stem_x, cy - stem_h + 6), (stem_x + 8, cy - stem_h + 13), color, 2)

        # Puntillo a la derecha si corresponde
        if "puntillo" in note_type:
            cv2.circle(frame, (cx + r + 6, cy), 2, color, -1)

        return frame

    def _draw_open_string_indicator(self, frame, scaled_pos, cur_x, cur_w, note_hit):
        cx, cy = scaled_pos
        color = config.color_hit if note_hit else (0, 255, 255)
        r = max(10, int(14 * self.scale))

        overlay = frame.copy()
        cv2.line(overlay, (cur_x, cy), (cur_x + cur_w, cy), color, max(2, int(4 * self.scale)))
        frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)

        cv2.circle(frame, (cx, cy), r, (0, 0, 0), 5)
        cv2.circle(frame, (cx, cy), r, color, 3)

        cv2.putText(
            frame,
            "0",
            (cx - int(5 * self.scale), cy + int(5 * self.scale)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5 * self.scale,
            color,
            2,
        )

        return frame

    @staticmethod
    def _overlay_png(background, overlay, x, y):
        h, w = overlay.shape[:2]
        bg_h, bg_w = background.shape[:2]

        # Evitar que se salga de los bordes de la ventana
        if x >= bg_w or y >= bg_h:
            return background
        if x + w > bg_w:
            w = bg_w - x
            overlay = overlay[:, :w]
        if y + h > bg_h:
            h = bg_h - y
            overlay = overlay[:h, :]

        # Si el PNG tiene canal alfa (transparencia)
        if overlay.shape[2] == 4:
            alpha = overlay[:, :, 3] / 255.0
            for c in range(3):
                background[y:y+h, x:x+w, c] = (
                    alpha * overlay[:, :, c] +
                    (1 - alpha) * background[y:y+h, x:x+w, c]
                )
        else:
            background[y:y+h, x:x+w] = overlay

        return background
