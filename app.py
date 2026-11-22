import sys
import cv2
import mediapipe as mp
import numpy as np
import os
import time
from config import config
from ranking import save_score
from ui_initializer import overlay_png
from song import clavelitos, cintas, alma


# Configuración de la tarea
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=config.model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2
)


# L2 Norm entre la mano y el punto objetivo (azul)
def calculate_distance(point1, point2) -> float:
    distance = np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
    return distance


# Inicializar landmarker
with HandLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(0)  # Abrir cámara
    timestamp=0
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:  # seguridad si la cámara no da fps
        fps = 30

    mp_hands = mp.solutions.hands

    frame_ms = int(1000 / fps)

    # MOVER ESTO A UI?
    # Cargar PNG manteniendo el canal alfa (transparencia)
    ruta_png = os.path.join(os.path.dirname(__file__), "images/bandurria_frame.png")
    img_png_raw = cv2.imread(ruta_png, cv2.IMREAD_UNCHANGED)
    base_w, base_h = 650,206
    base_x, base_y= 130,270
    fretboard_scale=1.0
    offset_x, offset_y= 0,0

  



    back = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
    color_normal = np.full_like(back, (255, 0, 0))   # Azul
    color_acierto = np.full_like(back, (0, 255, 0))  # Verde

    while cap.isOpened():

        selected_song=None
        song_finished=False
        score_saved=False
        player_name= ""
        top_scores=[]

        while cap.isOpened() and selected_song is None:

            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
            h, w, _ = frame.shape
            cur_w = min(w - 2, int(base_w * fretboard_scale))
            cur_h = min(h - 2, int(base_h * fretboard_scale))
            cur_x = int(np.clip(base_x - (cur_w - base_w) / 2 + offset_x, 0, max(0, w - cur_w)))
            cur_y = int(np.clip(base_y - (cur_h - base_h) / 2 + offset_y, 0, max(0, h - cur_h)))
            preview_png = cv2.resize(img_png_raw, (cur_w, cur_h))
            frame = overlay_png(frame, preview_png, x=cur_x, y=cur_y)
            
            cv2.putText(frame, "BANDURRIA HERO", (160, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 255), 3)
            cv2.putText(frame, f"1. {clavelitos.name} (Tempo: {clavelitos.tempo})", (100, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            cv2.putText(frame, f"2. {cintas.name} (Tempo: {cintas.tempo})", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            cv2.putText(frame, f"3. {alma.name} (Tempo: {alma.tempo})", (100, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

            cv2.putText(frame, f"Diapason [+/-] Zoom: {int(fretboard_scale*100)}% | [WASD] Mover | [R] Reset", (55, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.putText(frame, "Pulsa 1, 2 o 3 para jugar (ESC para salir)", (95, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            cv2.imshow("Hand Landmarker", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                selected_song = clavelitos
            elif key == ord('2'):
                selected_song = cintas
            elif key == ord('3'):
                selected_song = alma
            elif key == ord('+') or key == ord('=') or key == ord(']'):
              fretboard_scale = min(1.2, round(fretboard_scale + 0.05, 2))
            elif key == ord('-') or key == ord('['):
                fretboard_scale = max(0.6, round(fretboard_scale - 0.05, 2))
            elif key == ord('w') or key == ord('W'):
                offset_y -= 10
            elif key == ord('s') or key == ord('S'):
                offset_y += 10
            elif key == ord('a') or key == ord('A'):
                offset_x -= 10
            elif key == ord('d') or key == ord('D'):
                offset_x += 10
            elif key == ord('r') or key == ord('R'):
                fretboard_scale, offset_x, offset_y = 1.0, 0, 0
            elif key == 27 or cv2.getWindowProperty("Hand Landmarker", cv2.WND_PROP_VISIBLE) < 1:  # Tecla ESC
                cap.release()
                cv2.destroyAllWindows()
                sys.exit(0)
        if selected_song is None:
            break
        selected_song.reset()
        sum_t = counter = final_counter = 0
        note_hit = False
        circle_layer, circle_position, current_note_duration = selected_song.next_circle(cap)
        last_time = time.perf_counter()

        selected_song.play()
        

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            now = time.perf_counter()
            dt = now - last_time
            last_time = now
            sum_t += dt

            # Voltear frame horizontalmente
            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Dibuja el circulo en el frame
            h, w, _ = frame.shape
            cur_w = min(w - 2, int(base_w * fretboard_scale))
            cur_h = min(h - 2, int(base_h * fretboard_scale))
            img_png = cv2.resize(img_png_raw, (cur_w, cur_h))

            cur_x = int(np.clip(base_x - (cur_w - base_w) / 2 + offset_x, 0, max(0, w - cur_w)))
            cur_y = int(np.clip(base_y - (cur_h - base_h) / 2 + offset_y, 0, max(0, h - cur_h)))

            actual_dx = cur_x - int(base_x - (cur_w - base_w) / 2)
            actual_dy = cur_y - int(base_y - (cur_h - base_h) / 2)

            center_x = base_x + base_w / 2
            center_y = base_y + base_h / 2
            scaled_pos = (
                int(center_x + (circle_position[0] - center_x) * fretboard_scale + actual_dx),
                int(center_y + (circle_position[1] - center_y) * fretboard_scale + actual_dy),
            )

            circle_layer[:] = 0
            cv2.circle(circle_layer, scaled_pos, max(4, int(10 * fretboard_scale)), (255, 255, 255), -1)
            color_actual = color_acierto if note_hit else color_normal
            frame = np.where(circle_layer != 0, color_actual, frame)

            frame = overlay_png(frame, img_png, x=cur_x, y=cur_y)

            # Convertir frame a formato MediaPipe
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Ejecutar detección
            result = landmarker.detect_for_video(mp_image, timestamp)
            timestamp += frame_ms

            # Dibujar landmarks si los hay
            if result.hand_landmarks:
                for hand_landmarks in result.hand_landmarks:  # para mantener tu estructura
                    h, w, _ = frame.shape

                    # Dibuja líneas entre los landmarks
                    for connection in mp_hands.HAND_CONNECTIONS:
                        start_idx, end_idx = connection
                        start = hand_landmarks[start_idx]
                        end = hand_landmarks[end_idx]

                        x1, y1 = int(start.x * w), int(start.y * h)
                        x2, y2 = int(end.x * w), int(end.y * h)

                        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    # Dibuja los puntos (landmarks)
                    for idx, landmark in enumerate(hand_landmarks):
                        x, y = int(landmark.x * w), int(landmark.y * h)
                        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

                    hand_landmarks_list = [hand_landmarks[num] for num in [8, 12, 16, 20]] # índice, corazón, anular, meñique
                    landmarks_points = [(landmark.x, landmark.y) for landmark in hand_landmarks_list]
                    for landmark in landmarks_points:
                        h, w, _ = frame.shape
                        x, y = int(landmark[0] * w), int(landmark[1] * h)
                        if calculate_distance(landmark, (scaled_pos[0] / w, scaled_pos[1] / h)) < (0.05 * fretboard_scale) and not note_hit:
                            counter += 1
                            note_hit = True
                            break

            if not song_finished:
                if sum_t >= current_note_duration:
                    sum_t -= current_note_duration  # Evita desfase acumulado
                    try:
                        circle_layer, circle_position, current_note_duration = selected_song.next_circle(cap)
                        note_hit = False
                    except IndexError:
                        song_finished = True
                        selected_song.stop()
                else:
                    progreso = sum_t / current_note_duration
                    radius = int((10 + 30 * (1.0 - progreso)) * fretboard_scale)
                    cv2.circle(frame, scaled_pos, radius, (255, 255, 255), 2)

            end_time = time.time()

            # Mostrar tiempo restante de juego y puntos obtenidos
            cv2.putText(frame, f'Time: {config.game_time:.2f} - Points: {counter}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            config.game_time -= dt
            
            if song_finished:
                accuracy = (counter / len(selected_song.frets)) * 100
                frame = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
                cv2.putText(frame, f'Score: {counter} / {len(selected_song.frets)}', (150, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f'Accuracy: {accuracy:.1f}%', (150, 115), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                if not score_saved:
                    display_name = " ".join(player_name.ljust(3, "_"))
                    cv2.putText(frame, 'INTRODUCE TUS INICIALES:', (130, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(frame, display_name, (230, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 255), 3)
                    cv2.putText(frame, 'Pulsa ENTER para guardar', (140, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, f'TOP 3 - {selected_song.name}', (150, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                    for i, entry in enumerate(top_scores):
                        texto = f"{i+1}. {entry['name']} - {entry['score']}/{entry['total']} ({entry['accuracy']}%)"
                        cv2.putText(frame, texto, (140, 225 + i * 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

                    cv2.putText(frame, 'Pulsa ENTER para volver al menu', (100, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(frame, 'Pulsa ESC para salir', (150, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 128, 255), 2)
            
            cv2.imshow("Hand Landmarker", frame)
            # UN SOLO waitKey por fotograma
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or cv2.getWindowProperty("Hand Landmarker", cv2.WND_PROP_VISIBLE) < 1:  # ESC o cerrar la ventana
                selected_song.stop()
                cap.release()
                cv2.destroyAllWindows()
                sys.exit(0)
            elif not song_finished and (key == ord('+') or key == ord('=') or key == ord(']')):
                fretboard_scale = min(1.2, round(fretboard_scale + 0.05, 2))
            elif not song_finished and (key == ord('-') or key == ord('[')):
                fretboard_scale = max(0.6, round(fretboard_scale - 0.05, 2))
            elif not song_finished and (key == ord('w') or key == ord('W')):
                offset_y -= 10
            elif not song_finished and (key == ord('s') or key == ord('S')):
                offset_y += 10
            elif not song_finished and (key == ord('a') or key == ord('A')):
                offset_x -= 10
            elif not song_finished and (key == ord('d') or key == ord('D')):
                offset_x += 10
            elif not song_finished and (key == ord('r') or key == ord('R')):
                fretboard_scale, offset_x, offset_y = 1.0, 0, 0
            elif song_finished and not score_saved:
                if key==8:
                    player_name = player_name[:-1]
                elif key==13:
                    final_name=player_name if player_name else "AAA"
                    accuracy=(counter/len(selected_song.frets))*100
                    top_scores=save_score(selected_song.name, final_name, counter, len(selected_song.frets), accuracy)
                    score_saved=True
                elif len(player_name) < 3 and (65 <= key <= 90 or 97 <= key <= 122 or 48 <= key <= 57):
                    player_name+=chr(key).upper()
            elif song_finished and score_saved and key==13:
                selected_song.reset()
                break





    cap.release()
    cv2.destroyAllWindows()