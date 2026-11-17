import sys
import cv2
import mediapipe as mp
import numpy as np
import os
import time
from config import config, pos

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


#####################
#     CAMBIAR       #
#####################
# Crea una nueva capa y una posición random para el objetivo
def new_circle(padding) -> None:
    global circle_layer, circle_position
    circle_layer =  np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
    circle_position = (pos.fret[np.random.randint(0, 12)], pos.strings[np.random.randint(0, 6)])


# Inicializar landmarker
with HandLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(0)  # Abrir cámara
    selected_song=None
    while cap.isOpened() and selected_song is None:
        ret, frame = cap.read()
        if not ret:
            break
        frame=cv2.flip(frame,1)
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
        elif key == 27: # Tecla ESC
            sys.exit(0)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:  # seguridad si la cámara no da fps
        fps = 30

    mp_hands = mp.solutions.hands

    frame_ms = int(1000 / fps)

    # Inicializar valores
    timestamp = start_time = end_time = sum_t = counter = final_counter = 0

    blue_back = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
    blue_back[:] = (255, 0, 0)

    #######################
    #      MODIFICAR      #
    #######################
    new_circle(config.padding)

    # Cargar PNG manteniendo el canal alfa (transparencia)
    ruta_png = os.path.join(os.path.dirname(__file__), "images/bandurria_frame.png")
    img_png = cv2.imread(ruta_png, cv2.IMREAD_UNCHANGED)

    # Redimensionar el overlay para ajustarse a la bandurria
    img_png = cv2.resize(img_png, (650, 206))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Voltear frame horizontalmente
        frame = cv2.flip(frame, 1)

        ##########################################
        #    MODIFICAR PARA QUE NO SEA RANDOM    #
        ##########################################
        # Dibuja el circulo random en el frame
        cv2.circle(circle_layer, circle_position, 10, (255, 255, 255), -1)
        h, w = circle_layer.shape[:2]
        frame = np.where(circle_layer != 0, blue_back, frame)

        # Posición fija del overlay
        frame = overlay_png(frame, img_png, x=130, y=270)

        # Variables de tiempo
        t = end_time - start_time
        sum_t += t
        start_time = time.time()

        # Convertir frame a formato MediaPipe
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

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
                    if calculate_distance(landmark, (circle_position[0]/w, circle_position[1]/h)) < 0.05:
                        counter += 1
                        sum_t = 0
                        new_circle(config.padding)
                        break

        if sum_t > config.circle_time:
            sum_t = 0
            new_circle(config.padding)
        else:
            radius = int((20 + config.circle_time) - (config.circle_time_radius * (sum_t - config.circle_time)) / config.circle_time)
            cv2.circle(frame, circle_position, radius, (255, 255, 255), 2)

        end_time = time.time()

        # Mostrar tiempo restante de juego y puntos obtenidos
        cv2.putText(frame, f'Time: {config.game_time:.2f} - Points: {counter}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        config.game_time -= t
        
        if config.game_time <= 0:
            frame = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), dtype=np.uint8)
            cv2.putText(frame, f'Score: {final_counter} points', (180, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Press Enter to continue ...', (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Press ESC to exit', (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 128, 0), 2)

            # Tecla Enter para jugar
            if cv2.waitKey(1) & 0xFF == 13:
                config.game_time = 20
                counter = 0
            
            # Tecla ESC para salir
            if cv2.waitKey(1) & 0xFF == 27:
                sys.exit(0)
        else:
            final_counter = counter

        # Mostrar resultado
        cv2.imshow("Hand Landmarker", frame)

        # Tecla ESC para salir
        if cv2.waitKey(1) & 0xFF == 27:
            sys.exit(0)

    cap.release()
    cv2.destroyAllWindows()