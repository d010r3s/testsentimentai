import sqlite3, re, pandas as pd, spacy
from transformers import pipeline
nlp = spacy.load("ru_core_news_sm")
sent_pipe = pipeline("sentiment-analysis", model="cointegrated/rubert-tiny2")

PAT = re.compile(r"(доставк|скорост|поддержк|цен|удобств)", re.I)
def aspect(txt):
    doc = nlp(txt.lower())
    for chunk in doc.noun_chunks:
        if PAT.search(chunk.root.text):
            return chunk.text.strip()
    for tok in doc:
        if PAT.search(tok.text):
            return tok.lemma_
    return "прочее"

db = sqlite3.connect("sentiment.db")
df = pd.read_sql("SELECT * FROM reviews WHERE sentiment IS NULL", db)
if df.empty:
    print("➖ nothing new"); exit()

df["sentiment"] = df.text.map(lambda t: sent_pipe(t)[0]["label"].upper())
df["aspect"]    = df.text.map(aspect)
df.to_sql("reviews", db, if_exists="append", index=False)   # upsert-hack
print(f"✅ analysed {len(df)} rows")
