import flet as ft
from telegram_api import get_updates, send_message, load_all_history_from_db, save_message_to_db
import time
import threading

def main(page: ft.Page):
    page.title = "Панель Суфлёра Pixelka"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # --- UI Компоненты ---
    chats_list = ft.ListView(expand=1, spacing=10, padding=10, auto_scroll=True)
    messages_view = ft.ListView(expand=1, spacing=5, auto_scroll=True, padding=10)
    response_field = ft.TextField(hint_text="Ответ от имени Pixelka...", expand=True, border_radius=10)
    chat_title = ft.Text("Выберите диалог", size=20, weight=ft.FontWeight.BOLD)
    progress_ring = ft.ProgressRing()
    status_text = ft.Text("Загрузка истории из Supabase...")

    # --- Обработчики событий ---
    def on_chat_click(e):
        selected_id_str = str(e.control.data)
        page.session.set("selected_chat_id", selected_id_str)
        
        chat_title.value = f"Диалог с {e.control.text}"
        
        messages_view.controls.clear()
        history = page.session.get("conversations").get(selected_id_str, [])
        for msg_data in history:
            prefix = "👤 Пользователь:" if msg_data['is_user'] else "🤖 Pixelka (Вы):"
            messages_view.controls.append(ft.Text(f"{prefix} {msg_data['text']}", selectable=True))
        page.update()

    def send_click(e):
        chat_id_str = page.session.get("selected_chat_id")
        if chat_id_str and response_field.value:
            text_to_send = response_field.value
            chat_id = int(chat_id_str)
            
            send_message(chat_id, text_to_send)
            save_message_to_db(chat_id, text_to_send, is_user=False)
            
            conversations = page.session.get("conversations")
            conversations[chat_id_str].append({'text': text_to_send, 'is_user': False})
            
            prefix = "🤖 Pixelka (Вы):"
            messages_view.controls.append(ft.Text(f"{prefix} {text_to_send}", selectable=True))
            
            response_field.value = ""
            page.update()

    # --- Фоновый поток ---
    def update_checker():
        while True:
            last_id = page.session.get("last_update_id")
            offset = (last_id or 0) + 1
            updates = get_updates(offset)
            
            conversations = page.session.get("conversations")
            
            if updates: # Если пришли обновления
                for update in updates:
                    if 'message' in update and 'text' in update['message']:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        chat_id_str = str(chat_id)
                        user_name = msg['from'].get('first_name', 'User')
                        text = msg['text']
                        
                        save_message_to_db(chat_id, text, is_user=True, user_name=user_name)
                        
                        is_new_chat = chat_id_str not in conversations
                        if is_new_chat:
                            conversations[chat_id_str] = []
                            chats_list.controls.append(
                                ft.ElevatedButton(f"{user_name} ({chat_id_str})", on_click=on_chat_click, data=chat_id_str)
                            )
                        
                        conversations[chat_id_str].append({'text': text, 'is_user': True, 'user_name': user_name})

                        if page.session.get("selected_chat_id") == chat_id_str:
                            prefix = "👤 Пользователь:"
                            messages_view.controls.append(ft.Text(f"{prefix} {text}", selectable=True))
                    
                    if 'update_id' in update:
                        page.session.set("last_update_id", update['update_id'])
                
                page.update()
            
            time.sleep(3)

    # --- Инициализация ---
    def initialize():
        initial_history = load_all_history_from_db()
        if initial_history is None:
            status_text.value = "Ошибка: не удалось загрузить историю."
            status_text.color = ft.colors.RED
            progress_ring.visible = False
            page.update()
            return

        page.session.set("conversations", initial_history)
        
        for chat_id_str, messages in initial_history.items():
            user_name = "User"
            for msg in reversed(messages):
                if msg.get('user_name'):
                    user_name = msg['user_name']
                    break
            chats_list.controls.append(
                ft.ElevatedButton(f"{user_name} ({chat_id_str})", on_click=on_chat_click, data=chat_id_str)
            )
        
        page.session.set("last_update_id", 0)
        page.session.set("selected_chat_id", None)
        
        threading.Thread(target=update_checker, daemon=True).start()
        
        page.controls.clear()
        page.add(
            ft.Row(
                [
                    ft.Column([ft.Text("Диалоги:", weight=ft.FontWeight.BOLD), ft.Divider(), chats_list], width=300),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            chat_title,
                            messages_view,
                            ft.Row([response_field, ft.IconButton(ft.Icons.SEND, on_click=send_click, icon_size=30)])
                        ],
                        expand=True,
                    )
                ],
                expand=True,
            )
        )
        page.update()
        
    page.add(ft.Column([progress_ring, status_text], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    threading.Thread(target=initialize, daemon=True).start()

ft.app(target=main)
