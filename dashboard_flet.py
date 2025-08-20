import flet as ft
from telegram_api import get_updates, send_message, load_all_history_from_db, save_message_to_db
import time
import threading

# --- ГЛАВНАЯ ФУНКЦИЯ ПРИЛОЖЕНИЯ ---
def main(page: ft.Page):
    page.title = "Панель Суфлёра Pixelka"
    page.theme_mode = ft.ThemeMode.DARK

    # --- UI Компоненты ---
    chats_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
    messages_view = ft.ListView(expand=True, spacing=5, auto_scroll=True, padding=10)
    response_field = ft.TextField(hint_text="Ответ от имени Pixelka...", expand=True, border_radius=10)
    chat_title = ft.Text("Выберите диалог", size=20, weight=ft.FontWeight.BOLD)
    
    # --- Кнопка "Назад" для мобильного вида ---
    def back_to_list(e):
        left_column.visible = True
        right_column.visible = False
        page.update()

    back_button = ft.IconButton(ft.icons.ARROW_BACK, on_click=back_to_list)

    # --- Определяем наши колонки ---
    left_column = ft.Column(
        [
            ft.Text("Активные диалоги:", weight=ft.FontWeight.BOLD),
            ft.Divider(),
            chats_list
        ],
        width=300
    )
    
    right_column = ft.Column(
        [
            ft.Row([back_button, chat_title]), # Добавляем кнопку "Назад" к заголовку
            messages_view,
            ft.Row([response_field, ft.IconButton(ft.icons.SEND, on_click=lambda e: send_click(e), icon_size=30)])
        ],
        expand=True
    )

    # --- Главный контейнер ---
    main_layout = ft.Row([left_column, ft.VerticalDivider(), right_column], expand=True)

    # --- Обработчики событий ---
    def on_chat_click(e):
        selected_id_str = str(e.control.data)
        page.session.set("selected_chat_id", selected_id_str)
        chat_title.value = f"{e.control.text}" # Убрали "Диалог с" для краткости на мобилке
        
        messages_view.controls.clear()
        history = page.session.get("conversations").get(selected_id_str, [])
        for msg_data in history:
            prefix = "👤 Пользователь:" if msg_data['is_user'] else "🤖 Pixelka (Вы):"
            messages_view.controls.append(ft.Text(f"{prefix} {msg_data['text']}", selectable=True))

        # Адаптивность: на узком экране переключаем вид
        if page.width < 600:
            left_column.visible = False
            right_column.visible = True
        
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

    # --- Логика изменения размера окна/экрана ---
    def resize_layout(e):
        if page.width < 600: # Узкий экран
            left_column.width = None # Убираем фикс. ширину
            left_column.expand = True # Растягиваем на весь экран
            right_column.visible = False # Прячем правую колонку
            back_button.visible = True # Показываем кнопку "Назад"
            if len(main_layout.controls) > 1: # Убираем разделитель
                 if isinstance(main_layout.controls[1], ft.VerticalDivider):
                    main_layout.controls.pop(1)
        else: # Широкий экран
            left_column.width = 300 # Возвращаем фикс. ширину
            left_column.expand = False
            left_column.visible = True # Обе колонки видимы
            right_column.visible = True
            back_button.visible = False # Прячем кнопку "Назад"
            if len(main_layout.controls) == 1: # Возвращаем разделитель
                 main_layout.controls.insert(1, ft.VerticalDivider())
        page.update()

    page.on_resize = resize_layout

    # --- Фоновый поток ---
    def update_checker():
        while True:
            # Проверка, что страница еще существует, чтобы избежать ошибок
            if not page.session:
                break
                
            last_id = page.session.get("last_update_id")
            offset = (last_id or 0) + 1
            updates = get_updates(offset)
            
            conversations = page.session.get("conversations")
            
            if updates:
                new_messages_for_current_chat = False
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
                            new_messages_for_current_chat = True
                    
                    if 'update_id' in update:
                        page.session.set("last_update_id", update['update_id'])
                
                # Обновляем UI только если есть что обновлять
                if page.controls or new_messages_for_current_chat:
                    page.update()
            
            time.sleep(3)

    # --- Инициализация ---
    def initialize():
        page.add(ft.Column([ft.ProgressRing(), ft.Text("Загрузка истории...")], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        initial_history = load_all_history_from_db()

        if initial_history is None:
            page.clean()
            page.add(ft.Text("Ошибка: не удалось загрузить историю.", color=ft.colors.RED))
            page.update()
            return

        page.session.set("conversations", initial_history)
        
        for chat_id_str, messages in initial_history.items():
            user_name = "User"
            # Ищем последнее имя пользователя в истории чата
            for msg in reversed(messages):
                if msg.get('user_name'):
                    user_name = msg['user_name']
                    break
            chats_list.controls.append(
                ft.ElevatedButton(f"{user_name} ({chat_id_str})", on_click=on_chat_click, data=chat_id_str)
            )
        
        page.session.set("last_update_id", 0)
        page.session.set("selected_chat_id", None)
        
        # Запускаем фоновый поток
        threading.Thread(target=update_checker, daemon=True).start()
        
        # Очищаем страницу от "Загрузка..." и добавляем наш главный layout
        page.clean()
        page.add(main_layout)
        # Сразу вызываем resize, чтобы интерфейс подстроился под текущий размер экрана
        resize_layout(None)
        
    initialize()

# --- Точка входа в приложение ---
ft.app(target=main)
