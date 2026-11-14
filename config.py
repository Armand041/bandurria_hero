import os


class Config:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models/hand_landmarker.task')
        self.padding = 100
        self.game_time = 6000     # Duración del juego en segundos
        self.circle_time = 1    # Duración de cada circulo azul antes de que desaparezca
        self.circle_time_radius = 15


class Position:
    def __init__(self) -> None:
        self.strings = [0, 23, 41, 60, 79, 102]
        self.fret = [0, 28, 58, 85, 108, 134, 156, 176, 199, 215, 232, 250]

        self.real_distance = [300, 185]

        self.strings = [i + self.real_distance[0] for i in self.strings]
        self.fret = [j + self.real_distance[1] for j in self.fret]


pos = Position()
config = Config()  # Instancia única