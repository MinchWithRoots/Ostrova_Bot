import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from flask import Flask, request, json
import random
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация
VK_TOKEN = 'vk1.a.69EGRWB1sbkT5O5nNF5WLcI9rsjx9_gDHPEcWWAQvL26fMZVkzKmoHM4fBNQMGjLhkQDAD-0NU16OALmxM_HmsyF0gDykLWuIjU1YV5ZlyWqQZD_r_8qTKp8NYsH8-04_9d9q1UA6IvBbj4_qd8a5o_F4Fr75eSGKWyw0x1kt1XfhW_W3GEaEC_u2Nt2lcH7kv7qo8wdQatf6BzohS5asA'
CONFIRMATION_TOKEN = 'c9d9ac77'
SPREADSHEET_ID = '1bTxkAEKumsd1Cxnue0uxLzAWiEBe8OdAiKVio3LlFmg'

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Глобальные словари для хранения состояний
user_state = {}
user_data_cache = {}

# Настройки Google Sheets
SCOPES = ['https://spreadsheets.google.com/feeds', 
          'https://www.googleapis.com/auth/drive']
SHEET_NAMES = {
    'users': 'Users',
    'clubs': 'Clubs',
    'schedule': 'Club_Schedule',
    'events': 'Events',
    'registrations': 'Registrations',
    'faq': 'FAQ'
}

class GoogleSheetsManager:
    def __init__(self):
        self.connected = False
        self.sheets = {}
        self.connect()
    
    def connect(self, retries=3, delay=5):
        for attempt in range(retries):
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    'credentials.json', SCOPES)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(SPREADSHEET_ID)
                
                # Загружаем все листы
                self.sheets = {
                    'users': sheet.worksheet(SHEET_NAMES['users']),
                    'clubs': sheet.worksheet(SHEET_NAMES['clubs']),
                    'schedule': sheet.worksheet(SHEET_NAMES['schedule']),
                    'events': sheet.worksheet(SHEET_NAMES['events']),
                    'registrations': sheet.worksheet(SHEET_NAMES['registrations']),
                    'faq': sheet.worksheet(SHEET_NAMES['faq'])
                }
                self.connected = True
                logger.info("Успешное подключение к Google Sheets")
                return True
                
            except Exception as e:
                logger.error(f"Ошибка подключения к Google Sheets (попытка {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        
        self.connected = False
        return False
    
    def get_sheet(self, sheet_name):
        if not self.connected:
            if not self.connect():
                raise Exception("Не удалось подключиться к Google Sheets")
        
        return self.sheets.get(sheet_name)

# Инициализация менеджера Google Sheets
sheets_manager = GoogleSheetsManager()

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
        for time in times:
            kb.add_button(time)
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

# Функции для работы с Google Sheets
def is_user_registered(user_id):
    try:
        users_sheet = sheets_manager.get_sheet('users')
        users = users_sheet.get_all_records()
        return any(str(user['user_id']) == str(user_id) for user in users)
    except Exception as e:
        logger.error(f"Ошибка при проверке регистрации пользователя: {e}")
        return False

def register_user(user_id, first_name, last_name, birthdate, phone):
    try:
        users_sheet = sheets_manager.get_sheet('users')
        reg_date = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        users_sheet.append_row([
            str(user_id), 
            first_name, 
            last_name, 
            birthdate, 
            phone, 
            reg_date
        ])
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        return False

def get_active_clubs():
    try:
        clubs_sheet = sheets_manager.get_sheet('clubs')
        clubs = clubs_sheet.get_all_records()
        return [club for club in clubs if club.get('active', '').upper() == 'TRUE']
    except Exception as e:
        logger.error(f"Ошибка при получении активных кружков: {e}")
        return []

def get_club_dates(club_id):
    try:
        schedule_sheet = sheets_manager.get_sheet('schedule')
        schedules = schedule_sheet.get_all_records()
        club_schedules = [s for s in schedules if str(s.get('club_id')) == str(club_id)]
        
        dates = []
        for s in club_schedules:
            try:
                date_obj = datetime.strptime(s['date'], '%d.%m.%Y')
                dates.append({
                    'date': s['date'],
                    'display': f"{s['date']} ({s.get('day_of_week', '')})",
                    'schedule_id': s.get('club_id')
                })
            except ValueError:
                continue
        return dates
    except Exception as e:
        logger.error(f"Ошибка при получении дат кружка: {e}")
        return []

def get_schedule_times(schedule_id):
    try:
        schedule_sheet = sheets_manager.get_sheet('schedule')
        schedules = schedule_sheet.get_all_records()
        schedule = next(
            (s for s in schedules if str(s.get('club_id')) == str(schedule_id)), 
            None
        )
        if schedule:
            return [f"{schedule.get('start_time', '')}-{schedule.get('end_time', '')}"]
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении времени занятий: {e}")
        return []

def get_active_events():
    try:
        events_sheet = sheets_manager.get_sheet('events')
        events = events_sheet.get_all_records()
        return [event for event in events if event.get('active', '').upper() == 'TRUE']
    except Exception as e:
        logger.error(f"Ошибка при получении активных мероприятий: {e}")
        return []

def get_faq_categories():
    try:
        faq_sheet = sheets_manager.get_sheet('faq')
        faqs = faq_sheet.get_all_records()
        return list(set([faq.get('category', '') for faq in faqs if faq.get('category')]))
    except Exception as e:
        logger.error(f"Ошибка при получении категорий FAQ: {e}")
        return []

def get_faq_by_category(category):
    try:
        faq_sheet = sheets_manager.get_sheet('faq')
        faqs = faq_sheet.get_all_records()
        return [faq for faq in faqs if faq.get('category') == category]
    except Exception as e:
        logger.error(f"Ошибка при получении FAQ по категории: {e}")
        return []

def register_for_club(user_id, club_id, schedule_id):
    try:
        registrations_sheet = sheets_manager.get_sheet('registrations')
        schedule_sheet = sheets_manager.get_sheet('schedule')
        
        reg_date = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        reg_time = datetime.now().strftime('%H:%M:%S')
        
        # Добавляем запись о регистрации
        registrations_sheet.append_row([
            len(registrations_sheet.get_all_records()) + 1,
            str(user_id),
            'club',
            str(club_id),
            reg_date,
            reg_time,
            'active'
        ])
        
        # Обновляем количество участников
        schedules = schedule_sheet.get_all_records()
        for i, s in enumerate(schedules, start=2):
            if str(s.get('club_id')) == str(schedule_id):
                current = int(s.get('current_participants', 0)) if s.get('current_participants') else 0
                schedule_sheet.update_cell(i, 8, current + 1)
                break
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации на кружок: {e}")
        return False

def register_for_event(user_id, event_id):
    try:
        registrations_sheet = sheets_manager.get_sheet('registrations')
        events_sheet = sheets_manager.get_sheet('events')
        
        reg_date = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        reg_time = datetime.now().strftime('%H:%M:%S')
        
        registrations_sheet.append_row([
            len(registrations_sheet.get_all_records()) + 1,
            str(user_id),
            'event',
            str(event_id),
            reg_date,
            reg_time,
            'active'
        ])
        
        # Обновляем количество участников мероприятия
        events = events_sheet.get_all_records()
        for i, e in enumerate(events, start=2):
            if str(e.get('event_id')) == str(event_id):
                current = int(e.get('current_participants', 0)) if e.get('current_participants') else 0
                events_sheet.update_cell(i, 9, current + 1)
                break
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации на мероприятие: {e}")
        return False

def get_user_registrations(user_id):
    try:
        registrations_sheet = sheets_manager.get_sheet('registrations')
        clubs_sheet = sheets_manager.get_sheet('clubs')
        events_sheet = sheets_manager.get_sheet('events')
        
        registrations = registrations_sheet.get_all_records()
        user_regs = [
            r for r in registrations 
            if str(r.get('user_id')) == str(user_id) 
            and r.get('status', '').lower() == 'active'
        ]
        
        club_regs = []
        event_regs = []
        
        for reg in user_regs:
            if reg.get('type') == 'club':
                club = next(
                    (c for c in clubs_sheet.get_all_records() 
                     if str(c.get('club_id')) == str(reg.get('item_id'))),
                    None
                )
                if club:
                    club_regs.append(club.get('name', 'Неизвестный кружок'))
            
            elif reg.get('type') == 'event':
                event = next(
                    (e for e in events_sheet.get_all_records() 
                     if str(e.get('event_id')) == str(reg.get('item_id'))),
                    None
                )
                if event:
                    event_regs.append(
                        f"{event.get('name', 'Неизвестное мероприятие')} "
                        f"({event.get('date', 'без даты')})"
                    )
        
        return {
            'clubs': ', '.join(club_regs) if club_regs else 'Нет записей',
            'events': ', '.join(event_regs) if event_regs else 'Нет записей'
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
        data = json.loads(request.data)

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
                        users_sheet = sheets_manager.get_sheet('users')
                        users = users_sheet.get_all_records()
                        user = next(
                            (u for u in users 
                             if str(u.get('user_id')) == str(user_id)), 
                            None
                        )
                        
                        if user:
                            response = (
                                f"Ваши данные:\n"
                                f"Имя: {user.get('first_name', 'не указано')}\n"
                                f"Фамилия: {user.get('last_name', 'не указана')}\n"
                                f"Дата рождения: {user.get('birthdate', 'не указана')}\n"
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
                        f"Дата: {event.get('date', 'не указана')}\n"
                        f"Время: {event.get('time', 'не указано')}\n"
                        f"Место: {event.get('location', 'не указано')}\n"
                        f"Описание: {event.get('description', 'отсутствует')}\n\n"
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
                response = "Часто задаваемые вопросы:\n\n"
                for faq in faqs:
                    response += f"Q: {faq.get('question', 'Вопрос отсутствует')}\n"
                    response += f"A: {faq.get('answer', 'Ответ отсутствует')}\n\n"
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
