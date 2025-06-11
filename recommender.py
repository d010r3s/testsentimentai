from flask import Flask, request, jsonify
import sqlite3, json, numpy as np, faiss
from sentence_transformers import SentenceTransformer
import openai, os, textwrap

app   = Flask(__name__)
DB    = sqlite3.connect("sentiment.db", check_same_thread=False)
IDX   = faiss.read_index("cases.faiss") if os.path.exists("cases.faiss") else None
META  = json.loads(open("cases_meta.json", encoding="utf-8").read()) if IDX else []
ST   = SentenceTransformer("all-MiniLM-L6-v2")

PROMPT = textwrap.dedent("""
Ты — консультант сервиса.
Отзыв: "{review}"
Похожие случаи:
{examples}
Дай 2 шага решения и кратко объясни пользу.
""")

@app.route("/classify", methods=["POST"])
def classify():
    txt = request.json["text"]
    return jsonify({"sentiment": "NEG" if "!" in txt else "POS"})

@app.route("/recommend")
def recommend():
    review_id = int(request.args["review_id"])
    txt = DB.execute("SELECT text FROM reviews WHERE id=?", (review_id,)).fetchone()[0]

    examples = "-"
    if IDX:
        v   = ST.encode(txt).astype("float32")
        _, I = IDX.search(np.array([v]), k=min(3, IDX.ntotal))
        examples = "\n".join(f"- {META[i][1][:60]} … | Решение: {META[i][3]}"
                             for i in I[0])

    prompt = PROMPT.format(review=txt, examples=examples)
    msg = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}],
            max_tokens=180).choices[0].message.content.strip()

    DB.execute("INSERT INTO actions(review_id, reco) VALUES(?,?)", (review_id, msg))
    DB.commit()
    return jsonify({"review": txt, "recommendation": msg})

if __name__ == "__main__":
    app.run(port=8000)
