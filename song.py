import os
import pandas as pd


class Song:
    def __init__(self, song_file) -> None:

        self.check_file(song_file)  # Confirmamos que el archivo existe

        # Parseamos el nombre del archivo para conseguir el nombre y el tempo
        self.name, self.tempo = self.parse_filename(song_file)

        # Cargamos los datos que necesitemos
        self.frets = []
        self.strings = []
        self.load_csv(song_file)

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


clavelitos = Song("./songs/clavelitos-185.csv")
cintas = Song("./songs/las_cintas_de_mi_capa-130.csv")
alma = Song("./songs/alma_corazon_y_vida-160.csv")
