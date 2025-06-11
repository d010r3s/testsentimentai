import os
import json
import sqlite3
import logging
from flask import Flask, request, jsonify
import faiss
import torch
import textwrap
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# ──────────────────────────────────────────────────────────────
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ──────────────────────────────────────────────────────────────
# 1) Настраиваем локальную русскоязычную модель (облегчённая)
# Используем небольшой ruGPT-3 small, чтобы избежать сбоев и OOM на Windows
MODEL_NAME = "sberbank-ai/rugpt3small_based_on_gpt2"
DEVICE = 0 if torch.cuda.is_available() else -1
try:
    generator = pipeline(
        "text-generation",
        MODEL_NAME,
        device=DEVICE,
        do_sample=True,
        top_p=0.95,
        temperature=0.7
    )
    logging.info(f"Loaded text-generation pipeline: {MODEL_NAME}, device={DEVICE}")
except Exception:
    logging.exception("Ошибка при загрузке модели генерации текста, отключаем генерацию")
    generator = None  # отключаем генерацию при ошибке

# ──────────────────────────────────────────────────────────────
app = Flask(__name__)

# Подключаемся к базе
DB = sqlite3.connect("sentiment.db", check_same_thread=False)

# ──────────────────────────────────────────────────────────────
# Загружаем FAISS-индекс и метаданные
if os.path.exists("cases.faiss") and os.path.exists("cases_meta.json"):
    try:
        IDX = faiss.read_index("cases.faiss")
        with open("cases_meta.json", encoding="utf-8") as f:
            META = json.load(f)
        logging.info("FAISS-индекс и метаданные успешно загружены")
    except Exception:
        logging.exception("Ошибка при загрузке FAISS-индекса или метаданных")
        IDX, META = None, []
else:
    IDX, META = None, []
    logging.warning("FAISS-индекс или метаданные не найдены; примеры не добавятся в промпт")

# Модель для поиска похожих случаев
try:
    ST = SentenceTransformer("all-MiniLM-L6-v2")
    logging.info("SentenceTransformer успешно загружен")
except Exception:
    logging.exception("Ошибка при загрузке SentenceTransformer")
    ST = None

# Шаблон промпта (на русском)
PROMPT = textwrap.dedent(
    """
    Ты — консультант сервиса ППР.
    Отзыв: "{review}"
    Похожие случаи:
    {examples}
    Дай два конкретных шага решения и кратко объясни их пользу.
    """
)

# Глобальный обработчик исключений
@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Unhandled exception during request")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/recommend")
def recommend():
    review_id = request.args.get("review_id")
    if not review_id:
        return jsonify({"error": "Параметр review_id не указан"}), 400

    cur = DB.execute("SELECT text FROM reviews WHERE id = ?", (review_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": f"review_id={review_id} не найден"}), 404
    txt = row[0]

    # Поиск похожих случаев
    examples = ""
    if ST and IDX and META:
        try:
            emb = ST.encode([txt]).astype("float32")
            D, I = IDX.search(emb, 3)
            for i in I[0]:
                if isinstance(i, int) and 0 <= i < len(META):
                    examples += f"- {META[i].get('text','')}\n"
        except Exception:
            logging.exception("Ошибка при поиске похожих кейсов")

    # Генерируем рекомендацию или возвращаем кейсы
    msg = None
    if generator:
        try:
            prompt = PROMPT.format(review=txt, examples=examples)
            out = generator(prompt, max_length=128)
            gen = out[0].get("generated_text", "").strip()
            msg = gen[len(prompt):].strip() if gen.startswith(prompt) else gen
        except Exception:
            logging.exception("Ошибка при генерации текста")
            msg = None
    if not msg:
        msg = "Предложения по решению на основе похожих случаев:\n" + examples.strip()

    # Сохраняем рекомендации в БД
    try:
        DB.execute(
            "INSERT INTO actions(review_id, reco, status) VALUES (?, ?, 'NEW')",
            (review_id, msg)
        )
        DB.commit()
    except Exception:
        logging.exception("Ошибка при сохранении рекомендации в БД")

    return jsonify({"review": txt, "recommendation": msg})

if __name__ == "__main__":
    # слушаем на всех интерфейсах для совместимости
    app.run(host="0.0.0.0", port=8000, debug=True)
