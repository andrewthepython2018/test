import json
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import streamlit as st #1


if sys.platform == "emscripten":
    DATA_FILE = Path("/task_journal/tasks.json")
else:
    DATA_FILE = Path.home() / ".task_journal" / "tasks.json"

CATEGORIES = ["Учёба", "Личное", "Проекты", "Другое"]


def load_tasks():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def save_tasks(tasks):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_name(f"{uuid4().hex}.tmp")
    try:
        temporary_file.write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary_file.replace(DATA_FILE)
    finally:
        temporary_file.unlink(missing_ok=True)


def save_and_refresh(tasks):
    try:
        save_tasks(tasks)
    except OSError:
        st.error("Запись сохранить не удалось. Попробуйте ещё раз.")
        return
    st.rerun()


def task_status(task, today):
    if task["completed_on"]:
        return "Выполнено"
    if task["due"] and task["due"] < today.isoformat():
        return "Просрочено"
    return "Открыто"


def show_summary(tasks, today):
    done = sum(task_status(task, today) == "Выполнено" for task in tasks)
    overdue = sum(task_status(task, today) == "Просрочено" for task in tasks)
    opened, completed, late = st.columns(3)
    opened.metric("Открыто", len(tasks) - done)
    completed.metric("Выполнено", done)
    late.metric("Просрочено", overdue)

    if tasks:
        st.progress(done / len(tasks), text=f"Выполнено {done} из {len(tasks)}")

    show_weekly_chart(tasks, today)


def show_weekly_chart(tasks, last_day):
    first_day = last_day - timedelta(days=6)
    days = [(first_day + timedelta(days=offset)).isoformat() for offset in range(7)]
    counts = [sum(task["completed_on"] == day for task in tasks) for day in days]

    with st.expander("Выполнено за последние 7 дней"):
        if any(counts):
            st.bar_chart(
                {"Дата": days, "Задач": counts},
                x="Дата",
                y="Задач",
                height=210,
            )
        else:
            st.caption("Отметьте задачу выполненной, чтобы появилась диаграмма.")


def show_add_form(tasks):
    st.subheader("Новая задача")
    with st.form("add_task", clear_on_submit=True):
        title = st.text_input("Название", max_chars=120, placeholder="Например, решить три задачи по физике")
        left, right = st.columns(2)
        category = left.selectbox("Категория", CATEGORIES)
        due = right.date_input("Срок (необязательно)", value=None, format="DD.MM.YYYY")
        submitted = st.form_submit_button("Добавить задачу", type="primary")

    if submitted:
        if not title.strip():
            st.warning("Введите название задачи.")
            return
        task = {
            "id": uuid4().hex,
            "title": title.strip(),
            "category": category,
            "due": due.isoformat() if due else None,
            "completed_on": None,
        }
        save_and_refresh([*tasks, task])


def show_task(task, tasks, today):
    status = task_status(task, today)
    task_id = task["id"]
    due = date.fromisoformat(task["due"]) if task["due"] else None
    deadline = due.strftime("%d.%m.%Y") if due else "Без срока"
    completed = task["completed_on"] is not None

    with st.container(border=True):
        st.text(task["title"])
        st.caption(f"{task['category']} · {deadline} · {status}")
        button_label = "Вернуть в работу" if completed else "Отметить выполненной"
        if st.button(button_label, key=f"status_{task_id}"):
            task["completed_on"] = None if completed else today.isoformat()
            save_and_refresh(tasks)

        with st.expander("Изменить задачу"):
            with st.form(f"edit_{task_id}"):
                title = st.text_input("Название", value=task["title"], max_chars=120)
                category = st.selectbox("Категория", CATEGORIES, index=CATEGORIES.index(task["category"]))
                new_due = st.date_input("Срок (необязательно)", value=due, format="DD.MM.YYYY")
                edited = st.form_submit_button("Сохранить изменения")
            if edited:
                if title.strip():
                    task["title"] = title.strip()
                    task["category"] = category
                    task["due"] = new_due.isoformat() if new_due else None
                    save_and_refresh(tasks)
                else:
                    st.warning("Введите название задачи.")

            confirm = st.checkbox("Подтверждаю удаление", key=f"confirm_{task_id}")
            if st.button("Удалить задачу", key=f"delete_{task_id}", disabled=not confirm):
                save_and_refresh([item for item in tasks if item["id"] != task_id])


def show_tasks_tab():
    try:
        tasks = load_tasks()
    except (OSError, ValueError):
        st.error("Не удалось прочитать сохранённый журнал.")
        return

    today = date.today()
    show_summary(tasks, today)
    show_add_form(tasks)

    st.subheader("Список задач")
    if not tasks:
        st.caption("Добавьте первую задачу в форме выше.")
        return

    left, right = st.columns(2)
    selected_status = left.selectbox("Статус", ["Все", "Открытые", "Просроченные", "Выполненные"])
    selected_category = right.selectbox("Фильтр по категории", ["Все", *CATEGORIES])
    visible = []
    for task in tasks:
        status = task_status(task, today)
        if selected_category != "Все" and task["category"] != selected_category:
            continue
        if selected_status == "Открытые" and status == "Выполнено":
            continue
        if selected_status == "Просроченные" and status != "Просрочено":
            continue
        if selected_status == "Выполненные" and status != "Выполнено":
            continue
        visible.append(task)

    visible.sort(key=lambda task: (bool(task["completed_on"]), task["due"] or "9999-12-31"))
    if not visible:
        st.caption("По этим фильтрам задач нет.")
    for task in visible:
        show_task(task, tasks, today)


st.set_page_config(page_title="Журнал задач", page_icon="📋", layout="centered")
st.title("Журнал задач")
if sys.platform == "emscripten":
    st.caption("Записи сохраняются в этом браузере.")

# Для нового раздела добавьте название в st.tabs и свой блок with.
tasks_tab, = st.tabs(["Задачи"])
with tasks_tab:
    show_tasks_tab()
