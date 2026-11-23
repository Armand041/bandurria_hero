import time
import cv2
from config import config
from hand_tracker import HandTracker
from ranking import save_score
from song import alma, cintas, clavelitos
from ui import GameRenderer

SONGS = [clavelitos, cintas, alma]
SPEED_LEVELS = [0.25, 0.5, 0.75, 1.0]


def init_camera():
    cap = cv2.VideoCapture(0)
    fps = cap.get(cv2.CAP_PROP_FPS) or config.default_fps
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return cap, int(1000 / fps), frame_w, frame_h


def should_exit(key):
    return key == 27 or cv2.getWindowProperty(config.window_name, cv2.WND_PROP_VISIBLE) < 1


def handle_fretboard_controls(key, renderer):
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


def run_menu(cap, renderer):
    speed_idx = 3  # Empieza en -1
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            return None

        current_speed = SPEED_LEVELS[speed_idx]
        frame = cv2.flip(frame, 1)
        frame = renderer.draw_menu(frame, SONGS)
        cv2.imshow(config.window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if should_exit(key):
            return None

        if key in (ord("z"), ord("Z")):
            speed_idx = max(0, speed_idx - 1)
        elif key in (ord("x"), ord("X")):
            speed_idx = min(len(SPEED_LEVELS) - 1, speed_idx + 1)
        renderer.adjust_speed(SPEED_LEVELS[speed_idx])

        if key in (ord("1"), ord("2"), ord("3")):
            selected = SONGS[int(chr(key)) - 1]
            selected.set_speed(current_speed)
            return selected

        handle_fretboard_controls(key, renderer)
    return None


def run_game_session(cap, renderer, tracker, song, frame_ms, timestamp):
    song.reset()
    song.play()

    score = 0
    note_hit = False
    last_note_idx = -1
    song_finished = False
    score_saved = False
    player_name = ""
    top_scores = []
    last_time = time.perf_counter()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        now = time.perf_counter()
        dt = now - last_time
        last_time = now

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        detection_result = tracker.detect(frame, timestamp)
        timestamp += frame_ms

        current_audio_t = song.get_audio_time()
        state, circle_layer, circle_pos, progress, note_idx, note_type = song.get_note_at_time(current_audio_t, w, h)

        scaled_pos = None
        wait_time = 0.0

        if state == "WAITING":
            wait_time = max(0.0, song.start_offset - current_audio_t)
        elif state == "PLAYING":
            if note_idx != last_note_idx:
                note_hit = False
                last_note_idx = note_idx

            scaled_pos = renderer.get_scaled_note_position(circle_pos, w, h)
            if not note_hit and tracker.check_hit(detection_result, scaled_pos, frame.shape, renderer.scale):
                score += 1
                note_hit = True
        elif state == "FINISHED" and not song_finished:
            song_finished = True
            song.stop()

        config.game_time -= dt

        if not song_finished:
            frame = renderer.draw_gameplay(
                frame, circle_layer, scaled_pos, note_hit, progress, score, config.game_time, wait_time, note_type
            )
            renderer.draw_hand_landmarks(frame, detection_result, tracker.connections)
        else:
            frame = renderer.draw_game_over(
                frame.shape, song.name, score, len(song.frets), score_saved, player_name, top_scores
            )

        cv2.imshow(config.window_name, frame)
        key = cv2.waitKey(1) & 0xFF

        if should_exit(key):
            song.stop()
            return timestamp, False

        if not song_finished:
            handle_fretboard_controls(key, renderer)
        elif not score_saved:
            if key == 8:  # Backspace
                player_name = player_name[:-1]
            elif key == 13:  # Enter
                final_name = player_name if player_name else "AAA"
                accuracy = (score / len(song.frets)) * 100
                top_scores = save_score(song.name, final_name, score, len(song.frets), accuracy, song.speed)
                score_saved = True
            elif len(player_name) < 3 and (65 <= key <= 90 or 97 <= key <= 122 or 48 <= key <= 57):
                player_name += chr(key).upper()
        elif key == 13:  # Volver al menú tras guardar
            song.reset()
            return timestamp, True

    return timestamp, False


def main():
    tracker = HandTracker()
    cap, frame_ms, frame_w, frame_h = init_camera()
    renderer = GameRenderer(frame_w, frame_h)
    timestamp = 0

    try:
        while cap.isOpened():
            selected_song = run_menu(cap, renderer)
            if selected_song is None:
                break

            timestamp, keep_running = run_game_session(
                cap, renderer, tracker, selected_song, frame_ms, timestamp
            )
            if not keep_running:
                break
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
