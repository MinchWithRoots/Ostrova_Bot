from flask import Flask, request
import json
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import os
from datetime import datetime
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Загрузка переменных окружения
VK_TOKEN = os.getenv('VK_TOKEN')
CONFIRMATION_TOKEN = os.getenv('CONFIRMATION_TOKEN')
GS_CREDENTIALS_FILE = os.getenv('GS_CREDENTIALS_FILE')
GS_SPREADSHEET_ID = os.getenv('GS_SPREADSHEET_ID')

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Глобальные словари для состояний пользователей
user_state = {}
user_data_cache = {}

# Подключение к Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] 
creds = service_account.Credentials.from_service_account_file(
    GS_CREDENTIALS_FILE, scopes=SCOPES
)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


class GoogleSheetManager:
    def __init__(self):
        self.sheet = sheet

    def get_values(self, range_name):
        try:
            result = self.sheet.values().get(
                spreadsheetId=GS_SPREADSHEET_ID,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            logger.error(f"Ошибка при чтении из Google Sheets: {e}")
            return []

    def append_value(self, range_name, values):
        try:
            body = {
                'values': [values]
            }
            self.sheet.values().append(
                spreadsheetId=GS_SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Ошибка при записи в Google Sheets: {e}")
            return False

    def update_value(self, range_name, values):
        try:
            body = {
                'values': [values]
            }
            self.sheet.values().update(
                spreadsheetId=GS_SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Ошибка при обновлении в Google Sheets: {e}")
            return False


# Инициализация Google Sheets
gs_manager = GoogleSheetManager()


def is_user_registered(user_id):
    try:
        values = gs_manager.get_values('Users!A2:A')
        user_ids = [row[0] for row in values if row]
        return str(user_id) in user_ids
    except Exception as e:
        logger.error(f"Ошибка при проверке регистрации пользователя: {e}")
        return False


def register_user(user_id, first_name, last_name, birthdate, phone):
    try:
        values = [
            user_id,
            first_name,
            last_name,
            birthdate,
            phone,
            datetime.now().strftime('%d.%m.%Y')
        ]
        return gs_manager.append_value('Users!A:F', values)
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        return False


def get_keyboard(name, user_id=None):
    kb = VkKeyboard(one_time=False)
    if name == "null":
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)
    elif name == "main":
        kb.add_button('Личный кабинет')
        kb.add_line()
        kb.add_button('Кружки и Мероприятия')
        kb.add_line()
        kb.add_button('Вопросы')
    elif name == "personal_account":
        if is_user_registered(user_id):
            kb.add_button('Информация')
            kb.add_line()
            kb.add_button('Мои записи')
            kb.add_line()
            kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)
        else:
            kb.add_button('Зарегистрироваться')
            kb.add_line()
            kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)
    elif name == "edit_info":
        kb.add_button('Имя и Фамилия')
        kb.add_line()
        kb.add_button('Дата рождения')
        kb.add_line()
        kb.add_button('Номер телефона')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "get_name":
        kb.add_button('Взять с профиля', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "get_birthdate":
        kb.add_button('Взять с профиля', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "activities":
        kb.add_button('Кружок')
        kb.add_line()
        kb.add_button('Мероприятие')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)
    elif name == "clubs":
        clubs = get_active_clubs()
        for i, club in enumerate(clubs):
            if i > 0 and i % 2 == 0:
                kb.add_line()
            kb.add_button(club)
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "club_dates":
        club_id = user_state[user_id]['club_id']
        dates = get_club_dates(club_id)
        for date_info in dates:
            kb.add_button(date_info['display'])
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "club_times":
        schedule_id = user_state[user_id]['schedule_id']
        times = get_schedule_times(schedule_id)
        for time_str in times:
            kb.add_button(time_str)
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "confirm_registration":
        kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Не подтверждаю', color=VkKeyboardColor.NEGATIVE)
    elif name == "events":
        events = get_active_events()
        for event in events:
            kb.add_button(event)
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    elif name == "questions":
        kb.add_button('Часто задаваемые вопросы')
        kb.add_line()
        kb.add_button('Свой вопрос')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)
    elif name == "faq":
        categories = get_faq_categories()
        for category in categories:
            kb.add_button(category)
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    return kb


def get_active_clubs():
    values = gs_manager.get_values('Clubs!B2:B')
    return [row[0] for row in values if row]


def get_club_dates(club_id):
    values = gs_manager.get_values(f'Club_Schedule!A:E')
    dates = []
    for row in values:
        if row[1] == club_id:
            date_str = row[2]
            day_of_week = row[3]
            schedule_id = row[0]
            dates.append({
                'date': date_str,
                'display': f"{date_str} ({day_of_week})",
                'schedule_id': schedule_id
            })
    return dates


def get_schedule_times(schedule_id):
    values = gs_manager.get_values(f'Club_Schedule!A:E')
    for row in values:
        if row[0] == schedule_id:
            return [f"{row[3]}-{row[4]}"]
    return []


def get_active_events():
    values = gs_manager.get_values('Events!B2:B')
    return [row[0] for row in values if row]


def get_faq_categories():
    values = gs_manager.get_values('FAQ!A2:A')
    return list(set([row[0] for row in values if row]))


def get_faq_by_category(category):
    values = gs_manager.get_values('FAQ!A:E')
    return [{'question': row[1], 'answer': row[2]} for row in values if row and row[0] == category]


@app.route('/callback', methods=['POST', 'GET'])
def callback():
    data = request.get_json()
    if request.method == 'GET':
        return 'I am alive!', 200
    if 'type' not in data:
        return 'not vk', 200
    if data['type'] == 'confirmation':
        return CONFIRMATION_TOKEN, 200
    elif data['type'] == 'message_new':
        message = data['object']['message']['text']
        user_id = data['object']['message']['from_id']
        logger.info(f"Получено сообщение от {user_id}: {message}")

        # Основные команды вне состояния
        if message == "Начать":
            send_message(
                user_id,
                "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».",
                get_keyboard("main")
            )
            return 'ok', 200

        # Обработка состояний пользователя
        if user_id in user_state:
            state = user_state[user_id]['state']

            if state == 'waiting_for_name':
                names = message.split()
                if len(names) >= 2:
                    user_data_cache[user_id] = {
                        'first_name': names[0],
                        'last_name': ' '.join(names[1:]),
                        'birthdate': None,
                        'phone': None
                    }
                    user_state[user_id] = {'state': 'waiting_for_birthdate'}
                    send_message(
                        user_id,
                        "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)",
                        get_keyboard("get_birthdate", user_id)
                    )
                else:
                    send_message(
                        user_id,
                        "Пожалуйста, введите имя и фамилию через пробел (например: Иван Иванов)"
                    )
                return 'ok', 200

            elif state == 'waiting_for_birthdate':
                try:
                    datetime.strptime(message, '%d.%m.%Y')
                    user_data_cache[user_id]['birthdate'] = message
                    user_state[user_id] = {'state': 'waiting_for_phone'}
                    send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                except ValueError:
                    send_message(user_id, "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
                return 'ok', 200

            elif state == 'waiting_for_phone':
                user_data_cache[user_id]['phone'] = message
                if register_user(
                    user_id,
                    user_data_cache[user_id]['first_name'],
                    user_data_cache[user_id]['last_name'],
                    user_data_cache[user_id]['birthdate'],
                    user_data_cache[user_id]['phone']
                ):
                    send_message(user_id, "Спасибо за регистрацию!", get_keyboard("main"))
                else:
                    send_message(
                        user_id,
                        "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.",
                        get_keyboard("main")
                    )
                del user_state[user_id]
                del user_data_cache[user_id]
                return 'ok', 200

        # Основные команды
        if message == "На главную":
            send_message(
                user_id, 
                "Вот меню для получения информации:", 
                get_keyboard("main")
            )
        elif message == "Личный кабинет":
            if is_user_registered(user_id):
                send_message(
                    user_id, 
                    "Выберите действие", 
                    get_keyboard("personal_account", user_id)
                )
            else:
                send_message(
                    user_id, 
                    "У вас отсутствует личный кабинет! Зарегистрируйте его!", 
                    get_keyboard("personal_account", user_id)
                )
        elif message == "Зарегистрироваться":
            if is_user_registered(user_id):
                send_message(user_id, "Вы уже зарегистрированы.", get_keyboard("main"))
            else:
                user_state[user_id] = {'state': 'waiting_for_name'}
                send_message(
                    user_id,
                    "Введите ваше имя и фамилию через пробел или нажмите «Взять с профиля».",
                    get_keyboard("get_name", user_id)
                )

        # Кнопка "Взять с профиля"
        elif message == "Взять с профиля":
            try:
                info = vk.users.get(user_ids=user_id, fields="first_name,last_name,bdate")[0]
                user_data_cache[user_id] = {
                    'first_name': info.get('first_name'),
                    'last_name': info.get('last_name'),
                    'birthdate': info.get('bdate'),  # Может быть только год
                    'phone': None
                }

                # Если есть полная дата — сразу переходим к телефону
                if info.get('bdate') and '.' in info.get('bdate'):
                    user_state[user_id] = {'state': 'waiting_for_phone'}
                    send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                else:
                    user_state[user_id] = {'state': 'waiting_for_birthdate'}
                    send_message(
                        user_id,
                        "Дата рождения не найдена полностью. Введите её в формате ДД.ММ.ГГГГ",
                        get_keyboard("get_birthdate", user_id)
                    )

            except Exception as e:
                logger.error(f"Ошибка получения данных из ВК: {e}")
                send_message(user_id, "Не удалось получить данные из профиля.")

        return 'ok', 200


def send_message(user_id, message, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.getrandbits(64),
            keyboard=keyboard.get_keyboard() if keyboard else None
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
