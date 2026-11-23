import io
import os
import librosa
import numpy as np
import pandas as pd
import pygame
import soundfile as sf
from config import config

pygame.mixer.init()


class Song:
    def __init__(self, song_file, audio_file, start_offset=0.0) -> None:
        self._check_file(song_file)

        self.name, self.tempo = self._parse_filename(song_file)
        self.base_tempo_sec = 60 / self.tempo
        self.audio_file = audio_file
        self.base_start_offset = start_offset

        self.frets = []
        self.strings = []
        self.duration = []
        self._load_csv(song_file)

        self.Fpx, self.Spx = self.sf_to_px(self.frets, self.strings)
        self.nNote = 0

        self._audio_cache = {}
        self.speed = 1.0
        self.set_speed(1.0)

    def set_speed(self, speed):
        self.speed = round(float(speed), 2)
        self.tempo_sec = self.base_tempo_sec / self.speed
        self.start_offset = self.base_start_offset / self.speed

        self.start_times = []
        current_t = self.start_offset
        for dur in self.duration:
            self.start_times.append(current_t)
            current_t += dur * self.tempo_sec
        self.end_time = current_t

    def next_circle(self, frame_w, frame_h):
        if self.nNote == len(self.frets):
            raise IndexError(f"{self.nNote} out of index bounds")

        pos_f, pos_s = self.Fpx[self.nNote], self.Spx[self.nNote]
        circle_layer, circle_position = self.create_circle(pos_f, pos_s, frame_w, frame_h)
        note_duration = self.duration[self.nNote] * self.tempo_sec

        self.nNote += 1
        return circle_layer, circle_position, note_duration

    def _get_stretched_audio(self):
        """Devuelve el archivo original si speed == 1.0, o un buffer WAV estirado sin cambiar el tono."""
        if self.speed == 1.0:
            return self.audio_file

        if self.speed not in self._audio_cache:
            y, sr = librosa.load(self.audio_file, sr=None)
            y_stretched = librosa.effects.time_stretch(y, rate=self.speed)
            buf = io.BytesIO()
            sf.write(buf, y_stretched, sr, format="WAV")
            buf.seek(0)
            self._audio_cache[self.speed] = buf
        else:
            self._audio_cache[self.speed].seek(0)

        return self._audio_cache[self.speed]

    def play(self):
        audio_source = self._get_stretched_audio()
        pygame.mixer.music.load(audio_source)
        pygame.mixer.music.play()

    def stop(self):
        pygame.mixer.music.stop()

    def reset(self):
        self.nNote = 0
        self.stop()

    def get_audio_time(self):
        """Devuelve el tiempo actual de reproducción en segundos."""
        pos_ms = pygame.mixer.music.get_pos()
        return pos_ms / 1000.0 if pos_ms >= 0 else 0.0

    def get_note_at_time(self, current_time, frame_w, frame_h):
        """
        Devuelve: (estado, circle_layer, circle_pos, progress, note_index)
        estado puede ser: 'WAITING', 'PLAYING' o 'FINISHED'
        """
        if current_time < self.start_offset:
            return "WAITING", None, None, None, -1, None

        if current_time >= self.end_time:
            return "FINISHED", None, None, None, len(self.frets), None

        # Avanzar el índice si el audio ya superó la nota actual
        while (
            self.nNote < len(self.frets) - 1
            and current_time >= self.start_times[self.nNote + 1]
        ):
            self.nNote += 1

        raw_dur = self.duration[self.nNote]
        note_start = self.start_times[self.nNote]
        note_dur = raw_dur * self.tempo_sec
        progress = min(1.0, max(0.0, (current_time - note_start) / note_dur))

        pos_f, pos_s = self.Fpx[self.nNote], self.Spx[self.nNote]
        circle_layer, circle_position = self.create_circle(pos_f, pos_s, frame_w, frame_h)
        note_type = self.get_note_symbol_name(raw_dur)

        return "PLAYING", circle_layer, circle_position, progress, self.nNote, note_type

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

    @staticmethod
    def get_note_symbol_name(duration_beats):
        catalog = [
            (4.0, "redonda"),
            (3.0, "blanca_puntillo"),
            (2.0, "blanca"),
            (1.5, "negra_puntillo"),
            (1.0, "negra"),
            (0.75, "corchea_puntillo"),
            (0.5, "corchea"),
            (0.25, "semicorchea")
        ]

        closest = min(catalog, key=lambda item: abs(item[0] - duration_beats))
        return closest[1]

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


clavelitos = Song(
    f"{config.song_base_path}/clavelitos-185.csv",
    f"{config.song_base_path}/clavelitos.mp3",
    start_offset=5.25,
)
cintas = Song(
    f"{config.song_base_path}/las_cintas_de_mi_capa-130.csv",
    f"{config.song_base_path}/las_cintas_de_mi_capa.mp3",
    start_offset=3.25,
)
alma = Song(
    f"{config.song_base_path}/alma_corazon_y_vida-160.csv",
    f"{config.song_base_path}/alma_corazon_y_vida.mp3",
    start_offset=3.5,
)
