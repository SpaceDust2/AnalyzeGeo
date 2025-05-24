import streamlit as st
from model import ChatLLM
import time

st.set_page_config(
    page_title="YandexGPT Chat",
    page_icon="🤖",
    layout="wide"
)

# Инициализация модели


@st.cache_resource
def load_model():
    return ChatLLM(
        model_name="yandex/YandexGPT-5-Lite-8B-instruct",
        device="cuda",
        dtype="float16"
    )


# Заголовок
st.title("💬 Чат с YandexGPT-5-Lite")

# Инициализация сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    with st.spinner("Загрузка модели..."):
        st.session_state.model = load_model()

# Системный промпт
system_prompt = st.text_area(
    "Системный промпт",
    value="Ты — полезный ассистент, который всегда даёт точные и информативные ответы.",
    height=100
)

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод пользователя
if prompt := st.chat_input("Введите сообщение"):
    # Добавляем сообщение пользователя в историю
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Генерация ответа
    with st.chat_message("assistant"):
        with st.spinner("Генерация ответа..."):
            response = st.session_state.model.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=512,
                temperature=0.7
            )
            st.markdown(response)

    # Добавляем ответ ассистента в историю
    st.session_state.messages.append(
        {"role": "assistant", "content": response})

# Кнопка очистки истории
if st.button("Очистить историю"):
    st.session_state.messages = []
    st.rerun()
