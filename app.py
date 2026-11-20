import sys
import cv2
import mediapipe as mp
import numpy as np
import os
import time
from config import config

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
    img_png = cv2.imread(ruta_png, cv2.IMREAD_UNCHANGED)

    # Redimensionar el overlay para ajustarse a la bandurria
    img_png = cv2.resize(img_png, (650, 206))



    back = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
    color_normal = np.full_like(back, (255, 0, 0))   # Azul
    color_acierto = np.full_like(back, (0, 255, 0))  # Verde

    while cap.isOpened():
        selected_song=None
        song_finished=False
        while cap.isOpened() and selected_song is None:

            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

            cv2.putText(frame, "BANDURRIA HERO", (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            cv2.putText(frame, f"1. {clavelitos.name} (Tempo: {clavelitos.tempo})", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"2. {cintas.name} (Tempo: {cintas.tempo})", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"3. {alma.name} (Tempo: {alma.tempo})", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "Pulsa 1, 2 o 3 para jugar (ESC para salir)", (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow("Hand Landmarker", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                selected_song = clavelitos
            elif key == ord('2'):
                selected_song = cintas
            elif key == ord('3'):
                selected_song = alma
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
            cv2.circle(circle_layer, circle_position, 10, (255, 255, 255), -1)
            h, w = circle_layer.shape[:2]
            color_actual = color_acierto if note_hit else color_normal
            frame = np.where(circle_layer != 0, color_actual, frame)

            # Posición fija del overlay
            frame = overlay_png(frame, img_png, x=130, y=270)

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
                        if calculate_distance(landmark, (circle_position[0]/w, circle_position[1]/h)) < 0.05 and not note_hit:
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
                    radius = int(10 + 30 * (1.0 - progreso))
                    cv2.circle(frame, circle_position, radius, (255, 255, 255), 2)

            end_time = time.time()

            # Mostrar tiempo restante de juego y puntos obtenidos
            cv2.putText(frame, f'Time: {config.game_time:.2f} - Points: {counter}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            config.game_time -= dt
            
            if song_finished:
                accuracy = (counter / len(selected_song.frets)) * 100
                frame = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
                cv2.putText(frame, f'Score: {counter} / {len(selected_song.frets)}', (150, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f'Accuracy: {accuracy:.1f}%', (150, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(frame, 'Pulsa ENTER para volver al menu', (100, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(frame, 'Pulsa ESC para salir', (150, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 128, 255), 2)
            
            cv2.imshow("Hand Landmarker", frame)
            # UN SOLO waitKey por fotograma
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or cv2.getWindowProperty("Hand Landmarker", cv2.WND_PROP_VISIBLE) < 1:  # ESC o cerrar la ventana
                selected_song.stop()
                sys.exit(0)
            elif song_finished and key == 13:  # ENTER vuelve al menú
                selected_song.reset()
                break  # Sale del bucle de partida y vuelve al menú exterior




    cap.release()
    cv2.destroyAllWindows()