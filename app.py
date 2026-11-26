"""
Módulo principal de Bandurria Hero.
Gestiona la cámara web, la ventana a pantalla completa, el menú de selección,
el bucle de partida y la pantalla final de ranking.
"""

import time
import cv2
import numpy as np
import tkinter as tk
from config import config
from hand_tracker import HandTracker
from ranking import save_score
from song import alma, cintas, clavelitos
from ui import GameRenderer

SONGS = [clavelitos, cintas, alma]
SPEED_LEVELS = [0.25, 0.5, 0.75, 1.0]


def init_camera():
    """Inicializa la webcam y obtiene sus dimensiones y milisegundos por fotograma."""
    cap = cv2.VideoCapture(0)
    fps = cap.get(cv2.CAP_PROP_FPS) or config.default_fps
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return cap, int(1000 / fps), frame_w, frame_h


def should_exit(key):
    """Comprueba si el usuario ha pulsado ESC o ha cerrado la ventana."""
    return key == 27 or cv2.getWindowProperty(config.window_name, cv2.WND_PROP_VISIBLE) < 1


def handle_fretboard_controls(key, renderer):
    """Gestiona el escalado (+/-), desplazamiento (WASD) y reseteo (R) del diapasón."""
    if key in (ord("+"), ord("="), ord("]")):
        renderer.adjust_zoom(0.05)
    elif key in (ord("-"), ord("[")):
        renderer.adjust_zoom(-0.05)
    elif key in (ord("w"), ord("W")):
        renderer.move_fretboard(0, -10)
    elif key in (ord("s"), ord("S")):
        renderer.move_fretboard(0, 10)
    elif key in (ord("a"), ord("A")):
        renderer.move_fretboard(-10, 0)
    elif key in (ord("d"), ord("D")):
        renderer.move_fretboard(10, 0)
    elif key in (ord("r"), ord("R")):
        renderer.reset_transform()


def run_menu(cap, renderer, screen_w, screen_h):
    """Muestra el menú principal para elegir canción, velocidad y ajuste del diapasón."""
    speed_idx = 3  # Empieza en -1
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            return None

        current_speed = SPEED_LEVELS[speed_idx]
        frame = cv2.flip(frame, 1)
        frame = renderer.draw_menu(frame, SONGS)
        show_fullscreen_frame(frame, screen_w, screen_h)

        key = cv2.waitKey(1) & 0xFF
        if should_exit(key):
            return None

        if key in (ord("z"), ord("Z")):
            speed_idx = max(0, speed_idx - 1)
        elif key in (ord("x"), ord("X")):
            speed_idx = min(len(SPEED_LEVELS) - 1, speed_idx + 1)
        renderer.adjust_speed(SPEED_LEVELS[speed_idx])

        # Selección de canción mediante teclado numérico
        if key in (ord("1"), ord("2"), ord("3")):
            selected = SONGS[int(chr(key)) - 1]
            selected.set_speed(current_speed)
            return selected

        handle_fretboard_controls(key, renderer)
    return None


def run_game_session(cap, renderer, tracker, song, frame_ms, timestamp, screen_w, screen_h):
    """Ejecuta una partida completa: detección de mano, evaluación de notas y ranking final."""
    song.reset()
    song.play()

    score = 0
    note_hit = False
    last_note_idx = -1
    song_finished = False
    score_saved = False
    player_name = ""
    top_scores = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        # Detección de landmarks de la mano con MediaPipe
        detection_result = tracker.detect(frame, timestamp)
        timestamp += frame_ms
        # Consulta del estado y nota activa según el tiempo actual del audio
        current_audio_t = song.get_audio_time()
        state, circle_layer, circle_pos, progress, note_idx, note_type, is_open = song.get_note_at_time(current_audio_t, w, h)

        scaled_pos = None
        wait_time = 0.0

        if state == "WAITING" and current_audio_t is not None:
            wait_time = max(0.0, song.start_offset - current_audio_t)
        elif state == "PLAYING":
            # Al cambiar de nota se reinicia la bandera de acierto
            if note_idx != last_note_idx:
                note_hit = False
                last_note_idx = note_idx
            if circle_pos is not None:
                scaled_pos = renderer.get_scaled_note_position(circle_pos, w, h)
                # Comprobación de acierto (cuerda al aire o traste pisado)
                if not note_hit:
                    if is_open:
                        fretboard_rect = renderer._compute_fretboard_rect(w, h)[:4]
                        if tracker.check_open_hit(detection_result, scaled_pos, fretboard_rect, frame.shape, renderer.scale):
                            score += 1
                            note_hit = True
                    elif tracker.check_hit(detection_result, scaled_pos, frame.shape, renderer.scale):
                        score += 1
                        note_hit = True
        elif state == "FINISHED" and not song_finished:
            song_finished = True
            song.stop()
        # Cálculo del tiempo restante de la canción
        if current_audio_t is not None:
            song.time = max(0.0, (song.base_time / song.speed) - current_audio_t)
        else:
            song.time = 0.0
        # Renderizado de la partida o de la pantalla final
        if not song_finished:
            frame = renderer.draw_gameplay(
                frame, circle_layer, scaled_pos, note_hit, progress, score, song.time, wait_time, note_type, is_open
            )
            renderer.draw_hand_landmarks(frame, detection_result, tracker.connections)
        else:
            total_playable = sum(1 for f in song.frets if f!=-2)
            frame = renderer.draw_game_over(
                frame.shape, song.name, score, total_playable, score_saved, player_name, top_scores
            )

        show_fullscreen_frame(frame, screen_w, screen_h)
        key = cv2.waitKey(1) & 0xFF

        if should_exit(key):
            song.stop()
            return timestamp, False
        # Controles según el estado: ajuste del diapasón en partida o entrada de iniciales al terminar
        if not song_finished:
            handle_fretboard_controls(key, renderer)
        elif not score_saved:
            if key == 8:  # Backspace
                player_name = player_name[:-1]
            elif key == 13:  # Enter
                final_name = player_name if player_name else "AAA"
                total_playable = sum(1 for f in song.frets if f != -2)
                accuracy = (score / total_playable) * 100
                top_scores = save_score(song.name, final_name, score, total_playable, accuracy, song.speed)
                score_saved = True
            elif len(player_name) < 3 and (65 <= key <= 90 or 97 <= key <= 122 or 48 <= key <= 57):
                player_name += chr(key).upper()
        elif key == 13:  # Volver al menú tras guardar
            song.reset()
            return timestamp, True

    return timestamp, False


def setup_window():
    """Configura la ventana principal de OpenCV en modo pantalla completa."""
    cv2.namedWindow(config.window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        config.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
    )


def get_screen_size():
    """Obtiene la resolución actual del monitor mediante Tkinter."""
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.destroy()
    return w, h


def show_fullscreen_frame(frame, screen_w, screen_h):
    """Escala el fotograma manteniendo su proporción y lo centra con bandas negras."""
    h, w = frame.shape[:2]
    scale = min(screen_w / w, screen_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
    y_offset = (screen_h - new_h) // 2
    x_offset = (screen_w - new_w) // 2
    canvas[y_offset: y_offset + new_h, x_offset: x_offset + new_w] = resized

    cv2.imshow(config.window_name, canvas)


def main():
    """Inicialización de recursos y alternancia entre menú y partida."""
    tracker = HandTracker()
    cap, frame_ms, frame_w, frame_h = init_camera()
    renderer = GameRenderer(frame_w, frame_h)
    screen_w, screen_h = get_screen_size()
    timestamp = 0
    setup_window()

    try:
        while cap.isOpened():
            selected_song = run_menu(cap, renderer, screen_w, screen_h)
            if selected_song is None:
                break

            timestamp, keep_running = run_game_session(
                cap, renderer, tracker, selected_song, frame_ms, timestamp, screen_w, screen_h
            )
            if not keep_running:
                break
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
