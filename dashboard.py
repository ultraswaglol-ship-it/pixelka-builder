import streamlit as st
from telegram_api import get_updates, send_message
import time

# Настройка страницы
st.set_page_config(page_title="Панель Суфлёра Pixelka", layout="wide")
st.title("🤖 Панель Суфлёра для Pixelka")

# Инициализируем хранилище для наших диалогов и состояний
if 'conversations' not in st.session_state:
    st.session_state.conversations = {} # Словарь для хранения истории по chat_id
if 'last_update_id' not in st.session_state:
    st.session_state.last_update_id = None # Чтобы не получать старые сообщения

# --- ЛОГИКА ОБНОВЛЕНИЯ ДАННЫХ ---
def fetch_new_messages():
    offset = st.session_state.last_update_id + 1 if st.session_state.last_update_id else None
    updates = get_updates(offset)
    
    for update in updates:
        # Проверяем, есть ли в апдейте сообщение и текст
        if 'message' in update and 'text' in update['message']:
            message = update['message']
            chat_id = message['chat']['id']
            text = message['text']
            user_name = message['from'].get('first_name', 'User')

            # Создаем диалог, если его еще нет
            if chat_id not in st.session_state.conversations:
                st.session_state.conversations[chat_id] = {'messages': [], 'user_name': user_name}
            
            # Добавляем сообщение в историю
            st.session_state.conversations[chat_id]['messages'].append(f"👤 {user_name}: {text}")
        
        # Обновляем ID последнего апдейта
        st.session_state.last_update_id = update['update_id']

# Запускаем получение новых сообщений
with st.spinner('Проверяю новые сообщения...'):
    fetch_new_messages()

# --- ОТОБРАЖЕНИЕ ИНТЕРФЕЙСА ---

# Боковая панель со списком чатов
st.sidebar.header("Активные диалоги")
# Если чатов нет, показываем сообщение
if not st.session_state.conversations:
    st.sidebar.info("Ожидание новых сообщений...")

# Выбираем активный чат
# st.radio будет отображать имена пользователей, а возвращать их chat_id
chat_ids = {f"{conv['user_name']} ({chat_id})": chat_id for chat_id, conv in st.session_state.conversations.items()}
if chat_ids:
    selected_chat_label = st.sidebar.radio("Выберите чат:", options=chat_ids.keys())
    selected_chat_id = chat_ids[selected_chat_label]

    # Основное окно с историей чата
    st.header(f"Диалог с {selected_chat_label}")
    
    # Показываем историю сообщений
    message_history = "\n\n".join(st.session_state.conversations[selected_chat_id]['messages'])
    st.text_area("История", value=message_history, height=400, disabled=True)

    # Поле для ответа
    response_text = st.text_input("Ваш ответ от имени бота:", key=f"response_{selected_chat_id}")

    if st.button("Отправить ответ", key=f"send_{selected_chat_id}"):
        if response_text:
            # Отправляем сообщение через API
            send_message(selected_chat_id, response_text)
            # Добавляем наш ответ в историю для отображения
            st.session_state.conversations[selected_chat_id]['messages'].append(f"🤖 Pixelka (Вы): {response_text}")
            # Очищаем поле ввода
            st.rerun() # Обновляем страницу, чтобы увидеть наш ответ
        else:
            st.warning("Поле ответа не может быть пустым.")

# --- АВТООБНОВЛЕНИЕ СТРАНИЦЫ ---
# Простая реализация автообновления раз в 5 секунд
time.sleep(3)
st.rerun()