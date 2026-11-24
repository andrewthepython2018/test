# ЖУРНАЛ ЗАДАЧ — шаг 1: каркас приложения
# Заголовок страницы и одна вкладка. Запуск: streamlit run step1_start.py
import streamlit as st


st.set_page_config(page_title="Журнал задач", page_icon="📋", layout="centered")
st.title("Журнал задач")
st.caption("Здесь будут твои задачи.")

# st.tabs возвращает столько вкладок, сколько названий в списке.
# Запятая после tasks_tab распаковывает список из одного элемента.
tasks_tab, = st.tabs(["Задачи"])
with tasks_tab:
    st.write("Скоро здесь появится список задач.")
    if st.button("Нажми меня"):
        st.write("Скрипт выполнился заново, и кнопка вернула True.")
