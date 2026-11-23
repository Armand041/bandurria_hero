import os
import numpy as np
import pandas as pd
import pygame
from config import config

pygame.mixer.init()


class Song:
    def __init__(self, song_file, audio_file) -> None:
        self._check_file(song_file)

        self.name, self.tempo = self._parse_filename(song_file)
        self.tempo_sec = 60 / self.tempo
        self.audio_file = audio_file

        self.frets = []
        self.strings = []
        self.duration = []
        self._load_csv(song_file)

        self.Fpx, self.Spx = self.sf_to_px(self.frets, self.strings)
        self.nNote = 0

    def next_circle(self, frame_w, frame_h):
        if self.nNote == len(self.frets):
            raise IndexError(f"{self.nNote} out of index bounds")

        pos_f, pos_s = self.Fpx[self.nNote], self.Spx[self.nNote]
        circle_layer, circle_position = self.create_circle(pos_f, pos_s, frame_w, frame_h)
        note_duration = self.duration[self.nNote] * self.tempo_sec

        self.nNote += 1
        return circle_layer, circle_position, note_duration

    def play(self):
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.stop()

    def reset(self):
        self.nNote = 0
        self.stop()

    def _load_csv(self, song_file):
        song_data = pd.read_csv(song_file)
        self.frets = [f - 1 for f in song_data["Traste"].tolist()]
        self.strings = [s - 1 for s in song_data["Cuerda"].tolist()]
        self.duration = song_data["Duracion"].tolist()

    @staticmethod
    def _check_file(song_file):
        if not os.path.isfile(song_file):
            raise FileNotFoundError(f"No se encontró el archivo: {song_file}")

    @staticmethod
    def _parse_filename(song_file):
        filename = os.path.basename(song_file)
        name_wo_ext, _ = os.path.splitext(filename)
        name, tempo = name_wo_ext.rsplit("-", 1)
        return name, int(tempo)

    @classmethod
    def sf_to_px(cls, frets, strings):
        dict_f = {-2: 0, -1: 50}
        for n_f, offset in enumerate([0, 28, 58, 85, 108, 134, 156, 176, 199, 215, 232, 250]):
            dict_f[n_f] = offset + 185

        dict_s = {-2: 0}
        for n_s, offset in enumerate([0, 23, 41, 60, 79, 102]):
            dict_s[n_s] = offset + 300

        return [dict_f[pos] for pos in frets], [dict_s[pos] for pos in strings]

    @classmethod
    def create_circle(cls, pos_f, pos_s, frame_w, frame_h):
        circle_layer = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        return circle_layer, (pos_f, pos_s)


clavelitos = Song(f"{config.song_base_path}/clavelitos-185.csv", f"{config.song_base_path}/clavelitos.mp3")
cintas = Song(f"{config.song_base_path}/las_cintas_de_mi_capa-130.csv", f"{config.song_base_path}/las_cintas_de_mi_capa.mp3")
alma = Song(f"{config.song_base_path}/alma_corazon_y_vida-160.csv", f"{config.song_base_path}/alma_corazon_y_vida.mp3")
