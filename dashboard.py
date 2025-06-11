import streamlit as st
import sqlite3
import pandas as pd
import requests

# Подключение к локальной БД
db = sqlite3.connect("sentiment.db", check_same_thread=False)

st.title("Sentiment AI MVP")

# Загружаем все отзывы
data = pd.read_sql("SELECT * FROM reviews", db)
st.write(f"Всего отзывов: {len(data)}")
st.bar_chart(data.groupby("aspect")["id"].count())

# Выбор отзыва через selectbox
sel = st.selectbox(
    "Отзыв",
    options=data.id,
    format_func=lambda i: f"{i}: {data.set_index('id').loc[i, 'text'][:60]}…"
)

if st.button("Получить рекомендацию"):
    # Показываем индикатор загрузки
    with st.spinner('Запрос к сервису рекомендаций...'):
        try:
            response = requests.get(
                "http://127.0.0.1:8000/recommend",
                params={"review_id": sel},
                timeout=60  # увеличиваем таймаут до 60 секунд
            )
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Не удалось подключиться к сервису рекомендаций:\n{e}")
        else:
            if not response.ok:
                st.error(
                    f"⚠️ Сервис вернул HTTP {response.status_code}:\n{response.text}"
                )
            else:
                try:
                    reco_data = response.json()
                except ValueError as e:
                    st.error(f"⚠️ Ошибка разбора JSON:\n{e}")
                    st.code(response.text, language="json")
                else:
                    recommendation = reco_data.get("recommendation")
                    if recommendation:
                        st.success(recommendation)
                    else:
                        st.warning("В ответе нет поля `recommendation`:")
                        st.json(reco_data)
