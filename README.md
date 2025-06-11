# testsentimentai
test

настройка виртуального окружения:
```
cd \Users\username\Downloads\testsentimentai-main\testsentimentai-main
.\venv\Scripts\activate
```
в первом окне powershell:
```
pip install -r requirements.txt
python init_db.py
python fetch_reviews.py
sqlite3 sentiment.db ".read import_cases.sql"
python build_case_kb.py
python analyse.py
python recommender.py
```
во втором окне powershell:
```
streamlit run dashboard.py
```

