from flask import Flask, request
import json
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import logging
from datetime import datetime

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация из .env
VK_TOKEN = os.getenv('VK_TOKEN')
CONFIRMATION_TOKEN = os.getenv('CONFIRMATION_TOKEN')

DB_HOST = os.getenv('DB_HOST')  # mysql-ostrova.alwaysdata.net
DB_USER = os.getenv('DB_USER')  # ostrova
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')  # ostrova_base

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Глобальные словари для состояний пользователей
user_state = {}
user_data_cache = {}

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self, retries=3, delay=5):
        for attempt in range(retries):
            try:
                self.connection = pymysql.connect(
                    host=DB_HOST,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    cursorclass=DictCursor
                )
                logger.info("Успешное подключение к базе данных")
                return True
            except Exception as e:
                logger.error(f"Ошибка подключения к базе данных (попытка {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        return False

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                if commit:
                    self.connection.commit()
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                return None
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            raise

    def close(self):
        if self.connection:
            self.connection.close()

# Инициализация менеджера БД
db_manager = DatabaseManager()

def is_user_registered(user_id):
    try:
        query = "SELECT 1 FROM Users WHERE user_id = %s"
        result = db_manager.execute_query(query, (user_id,), fetch_one=True)
        return result is not None
    except Exception as e:
        logger.error(f"Ошибка при проверке регистрации пользователя: {e}")
        return False

def register_user(user_id, first_name, last_name, birthdate, phone):
    try:
        query = """
        INSERT INTO Users (user_id, first_name, last_name, birthdate, phone, reg_date)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
        """
        db_manager.execute_query(query, (user_id, first_name, last_name, birthdate, phone), commit=True)
        return True
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
            kb.add_button(club['name'])
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
            kb.add_button(event['name'])
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
    try:
        query = "SELECT * FROM Clubs WHERE active = TRUE"
        return db_manager.execute_query(query, fetch_all=True) or []
    except Exception as e:
        logger.error(f"Ошибка при получении активных кружков: {e}")
        return []

def get_club_dates(club_id):
    try:
        query = """
        SELECT 
            schedule_id, 
            date, 
            DAYNAME(date) as day_of_week, 
            start_time, 
            end_time 
        FROM Club_Schedule 
        WHERE club_id = %s AND date >= CURDATE()
        ORDER BY date
        """
        schedules = db_manager.execute_query(query, (club_id,), fetch_all=True) or []
        dates = []
        for s in schedules:
            date_str = s['date'].strftime('%d.%m.%Y')
            dates.append({
                'date': date_str,
                'display': f"{date_str} ({s['day_of_week']})",
                'schedule_id': s['schedule_id']
            })
        return dates
    except Exception as e:
        logger.error(f"Ошибка при получении дат кружка: {e}")
        return []

def get_schedule_times(schedule_id):
    try:
        query = """
        SELECT 
            TIME_FORMAT(start_time, '%H:%i') as start_time,
            TIME_FORMAT(end_time, '%H:%i') as end_time
        FROM Club_Schedule
        WHERE schedule_id = %s
        """
        schedule = db_manager.execute_query(query, (schedule_id,), fetch_one=True)
        if schedule:
            return [f"{schedule['start_time']}-{schedule['end_time']}"]
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении времени занятий: {e}")
        return []

def get_active_events():
    try:
        query = "SELECT * FROM Events WHERE active = TRUE AND date >= CURDATE()"
        return db_manager.execute_query(query, fetch_all=True) or []
    except Exception as e:
        logger.error(f"Ошибка при получении активных мероприятий: {e}")
        return []

def get_faq_categories():
    try:
        query = "SELECT DISTINCT category FROM FAQ"
        faqs = db_manager.execute_query(query, fetch_all=True) or []
        return [faq['category'] for faq in faqs if faq.get('category')]
    except Exception as e:
        logger.error(f"Ошибка при получении категорий FAQ: {e}")
        return []

def get_faq_by_category(category):
    try:
        query = "SELECT question, answer FROM FAQ WHERE category = %s"
        return db_manager.execute_query(query, (category,), fetch_all=True) or []
    except Exception as e:
        logger.error(f"Ошибка при получении FAQ по категории: {e}")
        return []

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
                    user_data_cache[user_id]['first_name'],
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
        if message == "Начать":
            send_message(
                user_id, 
                "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", 
                get_keyboard("main")
            )
        elif message == "На главную":
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
