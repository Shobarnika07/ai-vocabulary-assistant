import json
import os
import random
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "vocab_data.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"words": [], "stats": {"total_quizzes": 0, "total_correct": 0}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sm2_interval(easiness, repetitions):
    if repetitions == 0:
        return 1
    if repetitions == 1:
        return 3
    return max(1, round(3 * easiness))


@app.route("/")
def index():
    data = load_data()
    words = data["words"]
    total = len(words)
    learned = sum(1 for w in words if w["repetitions"] >= 3)
    reviewed_today = sum(
        1 for w in words
        if w.get("last_reviewed")
        and w["last_reviewed"][:10] == datetime.now().strftime("%Y-%m-%d")
    )
    due = [
        w for w in words
        if not w.get("next_review") or w["next_review"] <= datetime.now().isoformat()
    ]
    return render_template(
        "index.html",
        total=total,
        learned=learned,
        mastered=learned,
        due=len(due),
        reviewed_today=reviewed_today,
        words=words,
        due_words=due[:5],
    )


@app.route("/add", methods=["GET", "POST"])
def add_word():
    if request.method == "POST":
        word = request.form.get("word", "").strip()
        meaning = request.form.get("meaning", "").strip()
        example = request.form.get("example", "").strip()
        category = request.form.get("category", "general").strip()
        if word and meaning:
            data = load_data()
            new_word = {
                "id": len(data["words"]) + 1,
                "word": word,
                "meaning": meaning,
                "example": example,
                "category": category,
                "easiness": 2.5,
                "repetitions": 0,
                "next_review": datetime.now().isoformat(),
                "last_reviewed": None,
                "correct_count": 0,
                "wrong_count": 0,
                "created_at": datetime.now().isoformat(),
            }
            data["words"].append(new_word)
            save_data(data)
            return redirect(url_for("add_word"))
    return render_template("add.html")


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    data = load_data()
    words = data["words"]
    if len(words) < 4:
        return render_template("quiz.html", error="Add at least 4 words to start quizzes!")
    due = [
        w for w in words
        if not w.get("next_review") or w["next_review"] <= datetime.now().isoformat()
    ]
    if not due:
        due = words
    random.shuffle(due)
    question_word = due[0]
    wrong_options = [w for w in words if w["id"] != question_word["id"]]
    wrong_options = random.sample(wrong_options, min(3, len(wrong_options)))
    options = wrong_options + [question_word]
    random.shuffle(options)
    return render_template(
        "quiz.html",
        question=question_word,
        options=options,
        total=len(words),
        progress=None,
        answered=False,
        last_correct=None,
        last_word=None,
    )


@app.route("/quiz/answer", methods=["POST"])
def quiz_answer():
    data = load_data()
    word_id = int(request.form["word_id"])
    chosen_id = int(request.form["chosen_id"])
    is_correct = word_id == chosen_id
    data["stats"]["total_quizzes"] += 1
    if is_correct:
        data["stats"]["total_correct"] += 1
    for w in data["words"]:
        if w["id"] == word_id:
            if is_correct:
                w["correct_count"] += 1
                w["repetitions"] += 1
                w["easiness"] = max(1.3, w["easiness"] + 0.1)
            else:
                w["wrong_count"] += 1
                w["easiness"] = max(1.3, w["easiness"] - 0.2)
                w["repetitions"] = max(0, w["repetitions"] - 1)
            interval = sm2_interval(w["easiness"], w["repetitions"])
            w["next_review"] = (datetime.now() + timedelta(days=interval)).isoformat()
            w["last_reviewed"] = datetime.now().isoformat()
            break
    save_data(data)
    words = data["words"]
    if len(words) < 4:
        return render_template("quiz.html", error="Not enough words!", question=None, options=[], total=0, progress=None, answered=True)
    due = [
        w for w in words
        if not w.get("next_review") or w["next_review"] <= datetime.now().isoformat()
    ]
    if not due:
        due = words
    random.shuffle(due)
    next_word = due[0]
    wrong_options = [w for w in words if w["id"] != next_word["id"]]
    wrong_options = random.sample(wrong_options, min(3, len(wrong_options)))
    options = wrong_options + [next_word]
    random.shuffle(options)
    accuracy = round(data["stats"]["total_correct"] / max(1, data["stats"]["total_quizzes"]) * 100, 1)
    return render_template(
        "quiz.html",
        question=next_word,
        options=options,
        total=len(words),
        progress=accuracy,
        answered=False,
        last_correct=is_correct,
        last_word=[w for w in words if w["id"] == word_id][0],
    )


@app.route("/stats")
def stats():
    data = load_data()
    words = data["words"]
    total = len(words)
    accuracy = 0
    if data["stats"]["total_quizzes"] > 0:
        accuracy = round(data["stats"]["total_correct"] / data["stats"]["total_quizzes"] * 100, 1)
    categories = {}
    for w in words:
        cat = w.get("category", "general")
        categories.setdefault(cat, []).append(w)
    difficulty_levels = {"easy": 0, "medium": 0, "hard": 0}
    for w in words:
        if w["repetitions"] >= 5:
            difficulty_levels["easy"] += 1
        elif w["repetitions"] >= 2:
            difficulty_levels["medium"] += 1
        else:
            difficulty_levels["hard"] += 1
    return render_template(
        "stats.html",
        words=words,
        total=total,
        accuracy=accuracy,
        total_quizzes=data["stats"]["total_quizzes"],
        categories=categories,
        difficulty_levels=difficulty_levels,
    )


@app.route("/api/delete/<int:word_id>", methods=["DELETE"])
def delete_word(word_id):
    data = load_data()
    data["words"] = [w for w in data["words"] if w["id"] != word_id]
    save_data(data)
    return jsonify({"success": True})


@app.route("/api/import", methods=["POST"])
def import_words():
    words_text = request.form.get("words", "").strip()
    if not words_text:
        return jsonify({"error": "No words provided"}), 400
    data = load_data()
    count = 0
    for line in words_text.split("\n"):
        parts = line.strip().split(" - ")
        if len(parts) >= 2:
            new_word = {
                "id": len(data["words"]) + 1 + count,
                "word": parts[0].strip(),
                "meaning": parts[1].strip(),
                "example": parts[2].strip() if len(parts) > 2 else "",
                "category": "imported",
                "easiness": 2.5,
                "repetitions": 0,
                "next_review": datetime.now().isoformat(),
                "last_reviewed": None,
                "correct_count": 0,
                "wrong_count": 0,
                "created_at": datetime.now().isoformat(),
            }
            data["words"].append(new_word)
            count += 1
    save_data(data)
    return jsonify({"success": True, "imported": count})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
