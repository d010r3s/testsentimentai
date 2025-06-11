# testsentimentai
test
```
pip install -r requirements.txt
python init_db.py
python fetch_reviews.py
sqlite3 sentiment.db ".read import_cases.sql"
python build_case_kb.py
python analyse.py
python recommender.py
```
в отдельном окне:
```
streamlit run dashboard.py
```

