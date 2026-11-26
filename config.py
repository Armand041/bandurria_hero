"""
Configuración global de Bandurria Hero: rutas de recursos, parámetros de detección,
dimensiones base del diapasón y paleta de colores.
"""

import os


class Config:
    def __init__(self):
        # Paths
        self.base_dir = os.path.dirname(__file__)
        self.model_path = os.path.join(self.base_dir, 'models/hand_landmarker.task')
        self.fretboard_img_path = os.path.join(self.base_dir, "images/bandurria_frame.png")
        self.song_base_path = os.path.join(self.base_dir, "songs")

        # Ventana y cámara
        self.window_name = "Bandurria Hero"
        self.default_fps = 30

        # Tiempos y detección
        self.num_hands = 1
        self.hit_threshold = 0.05
        self.fingertip_indices = [8, 12, 16, 20]  # Índice, corazón, anular, meñique

        # Dimensiones base del diapasón
        self.fretboard_base_w = 650
        self.fretboard_base_h = 206
        self.fretboard_base_x = 130
        self.fretboard_base_y = 270
        self.min_scale = 0.6
        self.max_scale = 1.2

        # Colores (BGR)
        self.color_normal = (255, 0, 0)  # Azul
        self.color_hit = (0, 255, 0)     # Verde


config = Config()  # Instancia única
