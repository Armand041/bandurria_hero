"""
Gestión de persistencia del ranking en formato JSON.
Guarda el Top 3 de puntuaciones de forma independiente por canción y velocidad.
"""
import json
import os

RANKING_FILE = os.path.join(os.path.dirname(__file__), "ranking.json")


def load_ranking():
    """Carga el archivo ranking.json si existe; si no, devuelve un diccionario vacío."""
    if not os.path.exists(RANKING_FILE):
        return {}
    with open(RANKING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_score(song_name, name, score, total_notes, accuracy, velocity):
    """Registra una nueva puntuación, ordena el Top 3 por aciertos y precisión, y guarda el JSON."""
    data = load_ranking()
    speed_key = f"{velocity}x"
    # Garantiza compatibilidad si existía un formato previo para la canción
    song_scores = data.get(song_name)
    if not isinstance(song_scores,dict):
        song_scores={}
        data[song_name]= song_scores
    scores = song_scores.get(speed_key, [])

    scores.append({
        "name": name,
        "score": score,
        "total": total_notes,
        "accuracy": round(accuracy, 1),
    })
    scores.sort(key=lambda x: (x["score"], x["accuracy"]), reverse=True)
    song_scores[speed_key] = scores[:3]


    with open(RANKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return song_scores[speed_key]
