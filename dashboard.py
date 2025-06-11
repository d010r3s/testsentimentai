import streamlit as st, sqlite3, pandas as pd, requests
db = sqlite3.connect("sentiment.db")

st.title("Sentiment AI MVP")
data = pd.read_sql("SELECT * FROM reviews", db)
st.write("Всего отзывов:", len(data))
st.bar_chart(data.groupby("aspect")["id"].count())

sel = st.selectbox("Отзыв", options=data.id, format_func=lambda i: f"{i}: {data.set_index('id').loc[i,'text'][:60]}…")
if st.button("Получить рекомендацию"):
    reco = requests.get("http://localhost:8000/recommend", params={"review_id": sel}).json()
    st.success(reco["recommendation"])
