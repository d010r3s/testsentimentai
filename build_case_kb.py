import sqlite3, json, pathlib, faiss, numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
db    = sqlite3.connect("sentiment.db")

rows = db.execute("""
  SELECT r.id, r.text, r.aspect, a.reco
  FROM reviews r JOIN actions a ON a.review_id = r.id
  WHERE a.status='DONE'
""").fetchall()
if not rows:
    print("➖ нет кейсов DONE"); exit()

vecs = model.encode([r[1] for r in rows]).astype("float32")

index = faiss.IndexFlatL2(vecs.shape[1])
index.add(vecs)                       # сначала добавляем
faiss.write_index(index, "cases.faiss")  # потом сохраняем на диск

pathlib.Path("cases_meta.json").write_text(
    json.dumps(rows, ensure_ascii=False), encoding="utf-8")

print(f"✅ KB built with {len(rows)} cases")
