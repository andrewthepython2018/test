import math

import requests
import streamlit as st


API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


@st.cache_data(ttl=3600)
def get_rates():
    """Получает полный ответ API с датой и курсами."""

    response = requests.get(API_URL, timeout=15)
    response.raise_for_status()

    return response.json()


def convert_to_rubles(amount, currency):
    """Пересчитывает сумму с учётом номинала валюты."""

    rate = currency["Value"] / currency["Nominal"]
    return amount * rate


def main():
    st.set_page_config(page_title="Конвертер валют", layout="centered")
    st.title("Конвертер валют")
    st.write("Выберите валюту и узнайте стоимость суммы в рублях.")
    st.caption("Источник: [CBR-XML-Daily](https://www.cbr-xml-daily.ru/)")

    try:
        data = get_rates()
        currencies = data["Valute"]
        date = data["Date"][:10]
    except requests.exceptions.RequestException:
        st.error("Не удалось получить курсы валют из API.")
        st.info("Проверьте доступ к сервису и обновите страницу.")
        return
    except (ValueError, KeyError, TypeError):
        st.error("Сервис вернул данные в неожиданном формате.")
        return

    if not isinstance(currencies, dict) or not currencies:
        st.error("В ответе сервиса нет списка валют.")
        return

    st.caption(f"Дата курса: {date}")
    st.caption("Справочный расчёт, не курс обмена в банке.")

    codes = sorted(currencies)
    default_index = codes.index("USD") if "USD" in codes else 0

    with st.form("converter"):
        code = st.selectbox("Валюта", codes, index=default_index)
        amount = st.number_input(
            "Сумма в выбранной валюте",
            min_value=0.0,
            value=100.0,
            step=1.0,
            format="%.2f",
        )
        submitted = st.form_submit_button("Перевести в рубли")

    if submitted:
        if not math.isfinite(amount):
            st.error("Введите конечное число.")
            return

        try:
            currency = currencies[code]
            rubles = convert_to_rubles(amount, currency)
            rate = currency["Value"] / currency["Nominal"]
            name = currency["Name"]
        except (KeyError, TypeError, ZeroDivisionError):
            st.error("Для выбранной валюты пришли неполные данные.")
            return

        st.subheader(name)
        st.metric(f"{amount:.2f} {code} в рублях", f"{rubles:.2f} RUB")
        st.caption(f"Курс за 1 {code}: {rate:.4f} RUB")


if __name__ == "__main__":
    main()
