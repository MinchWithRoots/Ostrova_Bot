import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from flask import Flask, request, jsonify
import random
from datetime import datetime
import time
import logging
import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация из переменных окружения
VK_TOKEN = os.getenv('VK_TOKEN')
CONFIRMATION_TOKEN = os.getenv('CONFIRMATION_TOKEN')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Глобальные словари для хранения состояний
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

# Инициализация менеджера базы данных
db_manager = DatabaseManager()

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
        for i, date in enumerate(dates):
            if i > 0 and i % 2 == 0:
                kb.add_line()
            kb.add_button(date['display'])
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

# Функции для работы с базой данных
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

def register_for_club(user_id, club_id, schedule_id):
    try:
        # Проверяем, есть ли уже запись
        check_query = """
        SELECT 1 FROM Registrations 
        WHERE user_id = %s AND type = 'club' AND item_id = %s AND status = 'active'
        """
        existing = db_manager.execute_query(check_query, (user_id, club_id), fetch_one=True)
        if existing:
            return False  # Уже записан
        
        # Добавляем запись о регистрации
        reg_query = """
        INSERT INTO Registrations 
        (user_id, type, item_id, date, time, status) 
        VALUES (%s, 'club', %s, CURDATE(), CURTIME(), 'active')
        """
        db_manager.execute_query(reg_query, (user_id, club_id), commit=True)
        
        # Обновляем количество участников
        update_query = """
        UPDATE Club_Schedule 
        SET current_participants = current_participants + 1 
        WHERE schedule_id = %s
        """
        db_manager.execute_query(update_query, (schedule_id,), commit=True)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации на кружок: {e}")
        return False

def register_for_event(user_id, event_id):
    try:
        # Проверяем, есть ли уже запись
        check_query = """
        SELECT 1 FROM Registrations 
        WHERE user_id = %s AND type = 'event' AND item_id = %s AND status = 'active'
        """
        existing = db_manager.execute_query(check_query, (user_id, event_id), fetch_one=True)
        if existing:
            return False  # Уже записан
        
        # Добавляем запись о регистрации
        reg_query = """
        INSERT INTO Registrations 
        (user_id, type, item_id, date, time, status) 
        VALUES (%s, 'event', %s, CURDATE(), CURTIME(), 'active')
        """
        db_manager.execute_query(reg_query, (user_id, event_id), commit=True)
        
        # Обновляем количество участников мероприятия
        update_query = """
        UPDATE Events 
        SET current_participants = current_participants + 1 
        WHERE event_id = %s
        """
        db_manager.execute_query(update_query, (event_id,), commit=True)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации на мероприятие: {e}")
        return False

def get_user_registrations(user_id):
    try:
        # Получаем записи на кружки
        clubs_query = """
        SELECT c.name 
        FROM Registrations r
        JOIN Clubs c ON r.item_id = c.club_id
        WHERE r.user_id = %s AND r.type = 'club' AND r.status = 'active'
        """
        club_regs = db_manager.execute_query(clubs_query, (user_id,), fetch_all=True) or []
        
        # Получаем записи на мероприятия
        events_query = """
        SELECT e.name, e.date 
        FROM Registrations r
        JOIN Events e ON r.item_id = e.event_id
        WHERE r.user_id = %s AND r.type = 'event' AND r.status = 'active'
        """
        event_regs = db_manager.execute_query(events_query, (user_id,), fetch_all=True) or []
        
        # Форматируем результаты
        club_names = [reg['name'] for reg in club_regs]
        event_names = [
            f"{reg['name']} ({reg['date'].strftime('%d.%m.%Y')})"
            for reg in event_regs
        ]
        
        return {
            'clubs': ', '.join(club_names) if club_names else 'Нет записей',
            'events': ', '.join(event_names) if event_names else 'Нет записей'
        }
    except Exception as e:
        logger.error(f"Ошибка при получении регистраций пользователя: {e}")
        return {
            'clubs': 'Ошибка при получении данных',
            'events': 'Ошибка при получении данных'
        }

@app.route('/callback', methods=['POST'])
def callback():
    try:
        data = request.get_json()
        if 'type' not in data:
            return 'not vk', 200
        
        if data['type'] == 'confirmation':
            return CONFIRMATION_TOKEN, 200
        
        if data['type'] == 'message_new':
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
                
                elif state == 'waiting_for_question':
                    send_message(
                        user_id, 
                        "Спасибо за вопрос! Мы свяжемся с вами в ближайшее время.", 
                        get_keyboard("main")
                    )
                    del user_state[user_id]
                    return 'ok', 200
                
                elif state == 'waiting_for_club_date':
                    club_id = user_state[user_id]['club_id']
                    dates = get_club_dates(club_id)
                    selected_date = next((d for d in dates if d['display'] == message), None)
                    if selected_date:
                        user_state[user_id] = {
                            'state': 'waiting_for_club_time',
                            'club_id': club_id,
                            'schedule_id': selected_date['schedule_id']
                        }
                        send_message(
                            user_id, 
                            "Выберите время занятия:", 
                            get_keyboard("club_times", user_id)
                        )
                    else:
                        send_message(
                            user_id, 
                            "Пожалуйста, выберите дату из предложенных вариантов."
                        )
                    return 'ok', 200
                
                elif state == 'waiting_for_club_time':
                    schedule_id = user_state[user_id]['schedule_id']
                    times = get_schedule_times(schedule_id)
                    if message in times:
                        if register_for_club(user_id, user_state[user_id]['club_id'], schedule_id):
                            clubs = get_active_clubs()
                            club = next(
                                (c for c in clubs 
                                 if str(c['club_id']) == str(user_state[user_id]['club_id'])), 
                                None
                            )
                            if club:
                                send_message(
                                    user_id, 
                                    f"Вы успешно записаны на кружок {club['name']}!", 
                                    get_keyboard("main")
                                )
                            else:
                                send_message(
                                    user_id, 
                                    "Вы успешно записаны на кружок!", 
                                    get_keyboard("main")
                                )
                        else:
                            send_message(
                                user_id, 
                                "Произошла ошибка при записи. Пожалуйста, попробуйте позже.", 
                                get_keyboard("main")
                            )
                        del user_state[user_id]
                    else:
                        send_message(
                            user_id, 
                            "Пожалуйста, выберите время из предложенных вариантов."
                        )
                    return 'ok', 200
                
                elif state == 'waiting_for_event_confirmation':
                    if message == 'Подтверждаю':
                        event_id = user_state[user_id]['event_id']
                        if register_for_event(user_id, event_id):
                            events = get_active_events()
                            event = next(
                                (e for e in events 
                                 if str(e['event_id']) == str(event_id)), 
                                None
                            )
                            if event:
                                send_message(
                                    user_id, 
                                    f"Вы успешно записаны на мероприятие {event['name']}!", 
                                    get_keyboard("main")
                                )
                            else:
                                send_message(
                                    user_id, 
                                    "Вы успешно записаны на мероприятие!", 
                                    get_keyboard("main")
                                )
                        else:
                            send_message(
                                user_id, 
                                "Произошла ошибка при записи. Пожалуйста, попробуйте позже.", 
                                get_keyboard("main")
                            )
                    else:
                        send_message(user_id, "Запись отменена", get_keyboard("main"))
                    del user_state[user_id]
                    return 'ok', 200
            
            # Обработка основных команд
            if message == "Начать":
                send_message(
                    user_id, 
                    "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", 
                    get_keyboard("main")
                )
                return 'ok', 200
            
            elif message == "На главную":
                send_message(
                    user_id, 
                    "Вот меню для получения информации:", 
                    get_keyboard("main")
                )
                return 'ok', 200
            
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
            
            elif message == "Зарегистрироваться":
                user_state[user_id] = {'state': 'waiting_for_name'}
                send_message(
                    user_id, 
                    "Прежде чем производить запись на кружок или мероприятие давайте зарегистрируемся! Ваши фамилия и имя (через пробел)?", 
                    get_keyboard("get_name", user_id)
                )
                return 'ok', 200
            
            elif message == "Взять с профиля":
                if user_id in user_state:
                    state = user_state[user_id]['state']
                    if state == 'waiting_for_name':
                        try:
                            user_info = vk.users.get(
                                user_ids=user_id, 
                                fields='first_name,last_name,bdate'
                            )[0]
                            user_data_cache[user_id] = {
                                'first_name': user_info['first_name'],
                                'last_name': user_info['last_name'],
                                'birthdate': None,
                                'phone': None
                            }
                            user_state[user_id] = {'state': 'waiting_for_birthdate'}
                            send_message(
                                user_id, 
                                "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", 
                                get_keyboard("get_birthdate", user_id)
                            )
                        except Exception as e:
                            logger.error(f"Ошибка при получении данных профиля: {e}")
                            send_message(
                                user_id, 
                                "Не удалось получить данные из профиля. Введите имя и фамилию вручную."
                            )
                    elif state == 'waiting_for_birthdate':
                        try:
                            user_info = vk.users.get(
                                user_ids=user_id, 
                                fields='bdate'
                            )[0]
                            if 'bdate' in user_info:
                                user_data_cache[user_id]['birthdate'] = user_info['bdate']
                                user_state[user_id] = {'state': 'waiting_for_phone'}
                                send_message(
                                    user_id, 
                                    "Ваш номер телефона?", 
                                    get_keyboard("null")
                                )
                            else:
                                send_message(
                                    user_id, 
                                    "Дата рождения не указана в профиле. Введите вручную."
                                )
                        except Exception as e:
                            logger.error(f"Ошибка при получении даты рождения: {e}")
                            send_message(
                                user_id, 
                                "Не удалось получить данные из профиля. Введите дату рождения вручную."
                            )
                return 'ok', 200
            
            elif message == "Информация":
                if is_user_registered(user_id):
                    try:
                        query = """
                        SELECT first_name, last_name, birthdate, phone 
                        FROM Users 
                        WHERE user_id = %s
                        """
                        user = db_manager.execute_query(query, (user_id,), fetch_one=True)
                        if user:
                            response = (
                                f"Ваши данные:\n"
                                f"Имя: {user.get('first_name', 'не указано')}\n"
                                f"Фамилия: {user.get('last_name', 'не указана')}\n"
                                f"Дата рождения: {user['birthdate'].strftime('%d.%m.%Y') if user.get('birthdate') else 'не указана'}\n"
                                f"Телефон: {user.get('phone', 'не указан')}"
                            )
                            send_message(
                                user_id, 
                                response, 
                                get_keyboard("edit_info", user_id)
                            )
                        else:
                            send_message(
                                user_id, 
                                "Ваши данные не найдены", 
                                get_keyboard("personal_account", user_id)
                            )
                    except Exception as e:
                        logger.error(f"Ошибка при получении информации пользователя: {e}")
                        send_message(
                            user_id, 
                            "Ошибка при получении данных. Пожалуйста, попробуйте позже.", 
                            get_keyboard("personal_account", user_id)
                        )
                return 'ok', 200
            
            elif message == "Мои записи":
                if is_user_registered(user_id):
                    regs = get_user_registrations(user_id)
                    response = (
                        f"Ваши записи:\n"
                        f"Кружки: {regs['clubs']}\n"
                        f"Мероприятия: {regs['events']}"
                    )
                    send_message(
                        user_id, 
                        response, 
                        get_keyboard("personal_account", user_id)
                    )
                return 'ok', 200
            
            elif message == "Кружки и Мероприятия":
                send_message(
                    user_id, 
                    "Выберите о чем хотите посмотреть информацию", 
                    get_keyboard("activities", user_id)
                )
                return 'ok', 200
            
            elif message == "Кружок":
                if not is_user_registered(user_id):
                    send_message(
                        user_id, 
                        "У вас отсутствует личный кабинет! Зарегистрируйте его!", 
                        get_keyboard("personal_account", user_id)
                    )
                else:
                    send_message(
                        user_id, 
                        "Выберите интересующее вас направление", 
                        get_keyboard("clubs", user_id)
                    )
                return 'ok', 200
            
            elif message in [club['name'] for club in get_active_clubs()]:
                club = next(
                    (c for c in get_active_clubs() 
                     if c['name'] == message), 
                    None
                )
                if club:
                    user_state[user_id] = {
                        'state': 'waiting_for_club_date',
                        'club_id': club['club_id']
                    }
                    response = (
                        f"{club['name']}\n"
                        f"{club.get('description', 'Описание отсутствует')}\n"
                        f"Выберите дату занятия:"
                    )
                    send_message(
                        user_id, 
                        response, 
                        get_keyboard("club_dates", user_id)
                    )
                return 'ok', 200
            
            elif message == "Мероприятие":
                send_message(
                    user_id, 
                    "Выберите интересующее вас мероприятие", 
                    get_keyboard("events", user_id)
                )
                return 'ok', 200
            
            elif message in [event['name'] for event in get_active_events()]:
                event = next(
                    (e for e in get_active_events() 
                     if e['name'] == message), 
                    None
                )
                if event:
                    user_state[user_id] = {
                        'state': 'waiting_for_event_confirmation',
                        'event_id': event['event_id']
                    }
                    response = (
                        f"{event['name']}\n"
                        f"Дата: {event['date'].strftime('%d.%m.%Y') if event.get('date') else 'не указана'}\n"
                        f"Время: {event['time'].strftime('%H:%M') if event.get('time') else 'не указано'}\n"
                        f"Место: {event.get('location', 'не указано')}\n"
                        f"Описание: {event.get('description', 'отсутствует')}\n"
                        f"Подтвердите запись:"
                    )
                    send_message(
                        user_id, 
                        response, 
                        get_keyboard("confirm_registration", user_id)
                    )
                return 'ok', 200
            
            elif message == "Вопросы":
                send_message(
                    user_id, 
                    "Есть вопросы?", 
                    get_keyboard("questions", user_id)
                )
                return 'ok', 200
            
            elif message == "Часто задаваемые вопросы":
                send_message(
                    user_id, 
                    "Выберите категорию вопроса:", 
                    get_keyboard("faq", user_id)
                )
                return 'ok', 200
            
            elif message in get_faq_categories():
                faqs = get_faq_by_category(message)
                response = "Часто задаваемые вопросы:\n"
                for faq in faqs:
                    response += f"Q: {faq.get('question', 'Вопрос отсутствует')}\n"
                    response += f"A: {faq.get('answer', 'Ответ отсутствует')}\n"
                send_message(
                    user_id, 
                    response.strip(), 
                    get_keyboard("faq", user_id)
                )
                return 'ok', 200
            
            elif message == "Свой вопрос":
                user_state[user_id] = {'state': 'waiting_for_question'}
                send_message(
                    user_id, 
                    "Введите свой вопрос", 
                    get_keyboard("null")
                )
                return 'ok', 200
            
            elif message == "Назад":
                send_message(
                    user_id, 
                    "Возвращаемся назад", 
                    get_keyboard("main")
                )
                return 'ok', 200
            
            return 'ok', 200
    except Exception as e:
        logger.error(f"Ошибка в обработке запроса: {e}")
        return 'error', 500

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
