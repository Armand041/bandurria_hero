
import json
import os

RANKING_FILE = os.path.join(os.path.dirname(__file__), "ranking.json")

def load_ranking():
    if not os.path.exists(RANKING_FILE):
        return {}
    with open(RANKING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_score(song_name, name, score, total_notes, accuracy):
    data = load_ranking()
    scores = data.get(song_name, [])
    scores.append({
        "name": name,
        "score": score,
        "total": total_notes,
        "accuracy": round(accuracy, 1)
    })
    scores.sort(key=lambda x: (x["score"], x["accuracy"]), reverse=True)
    data[song_name] = scores[:3]

    with open(RANKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return data[song_name]