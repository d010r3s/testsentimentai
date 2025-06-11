import csv, sqlite3, datetime as dt
DB = "sentiment.db"

def load_csv():
    with open("sample_reviews.csv", newline="", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            yield (row["text"], row["source"], row["brand"],
                   row.get("created_at") or dt.datetime.utcnow().isoformat())

def main():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.executemany("""
        INSERT INTO reviews(text, source, brand, created_at)
        VALUES (?, ?, ?, ?)
    """, load_csv())
    conn.commit()
    print("✅ reviews appended")
if __name__ == "__main__":
    main()
