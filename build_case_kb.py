import sqlite3, numpy as np, faiss, json, pathlib
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
db = sqlite3.connect("sentiment.db")
rows = db.execute("""
  SELECT r.id, r.text, r.aspect, a.reco
  FROM reviews r JOIN actions a ON a.review_id=r.id
  WHERE a.status='DONE'
""").fetchall()
if not rows: print("➖ no solved cases"); exit()
vecs  = model.encode([r[1] for r in rows]).astype("float32")
faiss.write_index(faiss.IndexFlatL2(vecs.shape[1]), "cases.faiss")
faiss.read_index("cases.faiss").add(vecs)
pathlib.Path("cases_meta.json").write_text(json.dumps(rows, ensure_ascii=False))
print(f"✅ KB built with {len(rows)} cases")
