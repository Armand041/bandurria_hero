import os
import pandas as pd
import cv2
import numpy as np


class Song:
    def __init__(self, song_file) -> None:

        self.check_file(song_file)  # Confirmamos que el archivo existe

        # Parseamos el nombre del archivo para conseguir el nombre y el tempo
        self.name, self.tempo = self.parse_filename(song_file)

        # Cargamos los datos que necesitemos
        self.frets = []
        self.strings = []
        self.load_csv(song_file)

        self.Fpx, self.Spx = self.__class__.SF_to_px(self.frets, self.strings)

        self.nNote = 0

    # Carga en listas los datos de la cancion. Ahora solo Trastes y Cuerdas
    def load_csv(self, song_file):
        song_data = pd.read_csv(song_file)
        Tfrets = song_data["Traste"].tolist()
        Tstrings = song_data["Cuerda"].tolist()

        self.frets = [f - 1 for f in Tfrets]
        self.strings = [s - 1 for s in Tstrings]

    # Comprueba que el archivo exista
    def check_file(self, song_file):
        if not os.path.isfile(song_file):
            raise FileNotFoundError(f"No se encontró el archivo: {song_file}")

    # Saca el nombre y el tempo de la canción, devolviendo los valores
    def parse_filename(self, song_file):
        filename = os.path.basename(song_file)

        name_wo_ext, _ = os.path.splitext(filename)

        name, tempo = name_wo_ext.rsplit("-", 1)

        return name, int(tempo)

    @classmethod
    def SF_to_px(cls, frets, strings):

        dict_F = {-2: 0, -1: 50}

        nF = 0
        for i in [0, 28, 58, 85, 108, 134, 156, 176, 199, 215, 232, 250]:
            dict_F[nF] = i + 185
            nF += 1

        dict_S = {-2: 0}

        nS = 0
        for i in [0, 23, 41, 60, 79, 102]:
            dict_S[nS] = i + 300
            nS += 1

        Fpx = [dict_F[pos] for pos in frets]
        Spx = [dict_S[pos] for pos in strings]

        return Fpx, Spx

    @classmethod
    def create_circle(cls, posF, posS, cap):
        circle_layer = np.zeros(
            (int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 3),
            dtype=np.uint8
        )

        circle_position = (posF, posS)

        return circle_layer, circle_position

    def next_circle(self, cap):
        if self.nNote == len(self.frets):
            raise IndexError(f"{self.nNote} out of index bounds")

        posF, posS = self.Fpx[self.nNote], self.Spx[self.nNote]
        circle_layer, circle_position = self.create_circle(posF, posS, cap)

        self.nNote += 1

        return circle_layer, circle_position


clavelitos = Song("./songs/clavelitos-185.csv")
cintas = Song("./songs/las_cintas_de_mi_capa-130.csv")
alma = Song("./songs/alma_corazon_y_vida-160.csv")
