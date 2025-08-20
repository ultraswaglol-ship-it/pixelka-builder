import requests
import json
from supabase import create_client, Client

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
# Вставьте сюда ваши реальные данные
BOT_TOKEN = "8289882641:AAGemZ8pi6FWRUMLaqedBvr4fD6UFqRffKs"
SUPABASE_URL = "https://xyretyxfwjokxdocliuz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh5cmV0eXhmd2pva3hkb2NsaXV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NzQ5ODQsImV4cCI6MjA2MDI1MDk4NH0.TpfDw-rUvkLJlT1jsQZ9P60bzlsCMgQs3pOKhrIscaI"

# --- КОНФИГУРАЦИЯ ---
# Базовый URL для API Telegram
TELEGRAM_API_URL = f"https://api.telegram.org/bot8289882641:AAGemZ8pi6FWRUMLaqedBvr4fD6UFqRffKs/"
# Инициализация клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С TELEGRAM ---
def get_updates(offset=None):
    """Получает новые сообщения из Telegram."""
    # Используем низкий таймаут, чтобы приложение не "зависало"
    params = {'timeout': 1, 'offset': offset}
    try:
        response = requests.get(TELEGRAM_API_URL + "getUpdates", params=params)
        response.raise_for_status()  # Проверяем на ошибки HTTP (4xx или 5xx)
        return response.json().get('result', [])
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при получении обновлений: {e}")
        return []
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON от Telegram.")
        return []

def send_message(chat_id, text):
    """Отправляет сообщение пользователю от имени бота."""
    params = {'chat_id': chat_id, 'text': text}
    try:
        response = requests.post(TELEGRAM_API_URL + "sendMessage", params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при отправке сообщения: {e}")

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С SUPABASE ---
def load_all_history_from_db():
    """Загружает всю историю из Supabase и группирует по чатам."""
    try:
        response = supabase.table('support_chat_history').select("*").order('created_at').execute()
        
        history = {}
        for message in response.data:
            chat_id_str = str(message['chat_id'])
            if chat_id_str not in history:
                history[chat_id_str] = []
            
            history[chat_id_str].append({
                'text': message['message_text'],
                'is_user': message['is_user_message'],
                'user_name': message.get('user_name', 'User')
            })
        return history
    except Exception as e:
        # Проверяем, содержит ли ошибка 'Invalid API key'
        if 'Invalid API key' in str(e):
            print("\n!!! ОШИБКА: Неверный URL или ключ API для Supabase. Проверьте ваши данные. !!!\n")
        else:
            print(f"Ошибка загрузки истории из Supabase: {e}")
        return None # Возвращаем None при ошибке, чтобы основной скрипт мог это обработать

def save_message_to_db(chat_id, text, is_user, user_name=None):
    """Сохраняет одно сообщение в базу данных Supabase."""
    try:
        supabase.table('support_chat_history').insert({
            'chat_id': chat_id,
            'message_text': text,
            'is_user_message': is_user,
            'user_name': user_name
        }).execute()
    except Exception as e:
        print(f"Ошибка сохранения сообщения в Supabase: {e}")


# --- ТЕСТОВЫЙ БЛОК ---
# Этот код выполнится, только если запустить этот файл напрямую: python telegram_api.py
if __name__ == "__main__":
    print("--- Запускаю тест файла telegram_api.py ---")
    
    # 1. Проверка ключей
    if not BOT_TOKEN or "ВАШ" in BOT_TOKEN:
        print("ОШИБКА: Пожалуйста, впишите ваш BOT_TOKEN.")
    if not SUPABASE_URL or "ВАШ" in SUPABASE_URL:
        print("ОШИБКА: Пожалуйста, впишите ваш SUPABASE_URL.")
    if not SUPABASE_KEY or "ВАШ" in SUPABASE_KEY:
        print("ОШИБКА: Пожалуйста, впишите ваш SUPABASE_KEY.")
    
    # 2. Тест соединения с Supabase
    print("\nШаг 1: Пробую соединиться с Supabase...")
    history = load_all_history_from_db()
    
    if history is not None:
        print("...Соединение с Supabase успешно!")
        print(f"   - Загружено {len(history)} диалогов.")
        
        # 3. Тест соединения с Telegram
        print("\nШаг 2: Пробую получить обновления от Telegram...")
        updates = get_updates()
        if updates is not None:
             print("...Соединение с Telegram успешно!")
             print(f"   - Получено {len(updates)} новых событий.")
        else:
            print("...ОШИБКА при соединении с Telegram.")

    else:
        print("...ОШИБКА при соединении с Supabase. Дальнейшие тесты отменены.")
    
    print("\n--- Тестирование завершено ---")