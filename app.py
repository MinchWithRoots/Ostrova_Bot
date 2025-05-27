from flask import Flask, request, json
import random
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Конфигурация
confirmation_token = 'c9d9ac77'
token = 'vk1.a.69EGRWB1sbkT5O5nNF5WLcI9rsjx9_gDHPEcWWAQvL26fMZVkzKmoHM4fBNQMGjLhkQDAD-0NU16OALmxM_HmsyF0gDykLWuIjU1YV5ZlyWqQZD_r_8qTKp8NYsH8-04_9d9q1UA6IvBbj4_qd8a5o_F4Fr75eSGKWyw0x1kt1XfhW_W3GEaEC_u2Nt2lcH7kv7qo8wdQatf6BzohS5asA'

# Инициализация VK API
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

# Инициализация Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1bTxkAEKumsd1Cxnue0uxLzAWiEBe8OdAiKVio3LlFmg/edit#gid=0')

# Получаем все листы
users_sheet = sheet.worksheet("Users")
clubs_sheet = sheet.worksheet("Clubs")
schedule_sheet = sheet.worksheet("Club_Schedule")
events_sheet = sheet.worksheet("Events")
registrations_sheet = sheet.worksheet("Registrations")
faq_sheet = sheet.worksheet("FAQ")

# Глобальные переменные для хранения состояний
user_state = {}
user_data = {}

# Функции для работы с таблицами
def get_user_data(user_id):
    try:
        records = users_sheet.get_all_records()
        for record in records:
            if str(record['user_id']) == str(user_id):
                return record
        return None
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

def register_user(user_id, first_name, last_name, birthdate, phone):
    try:
        users_sheet.append_row([
            user_id, first_name, last_name, 
            birthdate, phone,
            datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d.%m.%Y %H:%M")
        ])
        return True
    except Exception as e:
        print(f"Error registering user: {e}")
        return False

def get_active_clubs():
    try:
        clubs = clubs_sheet.get_all_records()
        return [club for club in clubs if club.get('active', 'TRUE') == 'TRUE']
    except Exception as e:
        print(f"Error getting clubs: {e}")
        return []

def get_club_schedule(club_id):
    try:
        schedule = schedule_sheet.get_all_records()
        today = datetime.now().strftime("%d.%m.%Y")
        return [s for s in schedule if str(s['club_id']) == str(club_id) and s['date'] >= today]
    except Exception as e:
        print(f"Error getting schedule: {e}")
        return []

def register_for_club(user_id, club_id, date, time):
    try:
        reg_id = len(registrations_sheet.get_all_records()) + 1
        registrations_sheet.append_row([
            reg_id, user_id, 'club', club_id, date, time, 'active'
        ])
        return True
    except Exception as e:
        print(f"Error registering for club: {e}")
        return False

def get_active_events():
    try:
        events = events_sheet.get_all_records()
        return [event for event in events if event.get('active', 'TRUE') == 'TRUE']
    except Exception as e:
        print(f"Error getting events: {e}")
        return []

def register_for_event(user_id, event_id):
    try:
        event = next((e for e in get_active_events() if str(e['event_id']) == str(event_id)), None)
        if event:
            reg_id = len(registrations_sheet.get_all_records()) + 1
            registrations_sheet.append_row([
                reg_id, user_id, 'event', event_id, 
                event['date'], event['time'], 'active'
            ])
            return True
        return False
    except Exception as e:
        print(f"Error registering for event: {e}")
        return False

def get_user_registrations(user_id):
    try:
        registrations = registrations_sheet.get_all_records()
        user_regs = [r for r in registrations if str(r['user_id']) == str(user_id) and r['status'] == 'active']
        
        club_reg = next((r for r in user_regs if r['type'] == 'club'), None)
        event_reg = next((r for r in user_regs if r['type'] == 'event'), None)
        
        return {
            'club': club_reg,
            'event': event_reg
        }
    except Exception as e:
        print(f"Error getting user registrations: {e}")
        return {'club': None, 'event': None}

# Функции для клавиатур
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
        if get_user_data(user_id):
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
        for club in clubs:
            kb.add_button(club['name'])
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "club_dates":
        # Это будет создаваться динамически
        pass

    elif name == "club_times":
        # Это будет создаваться динамически
        pass

    elif name == "confirm_registration":
        kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Не подтверждаю', color=VkKeyboardColor.NEGATIVE)

    elif name == "events":
        events = get_active_events()
        if len(events) == 1:
            # Обрабатывается отдельно
            pass
        else:
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
        faqs = faq_sheet.get_all_records()
        for faq in faqs:
            kb.add_button(faq['question'])
            kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    return kb

def get_club_dates_keyboard(club_id):
    kb = VkKeyboard(one_time=False)
    schedule = get_club_schedule(club_id)
    for s in schedule:
        date_obj = datetime.strptime(s['date'], '%d.%m.%Y')
        day_name = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'][date_obj.weekday()]
        kb.add_button(f"{s['date']} ({day_name})")
        kb.add_line()
    kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    return kb

def get_club_times_keyboard(club_id, date):
    kb = VkKeyboard(one_time=False)
    schedule = get_club_schedule(club_id)
    times = []
    for s in schedule:
        if s['date'] == date:
            times.append(s['start_time'])
    
    for time in sorted(times):
        kb.add_button(time)
        kb.add_line()
    kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
    return kb

def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.getrandbits(64),
        keyboard=keyboard.get_keyboard() if keyboard else None
    )

# Обработчик вебхука
@app.route('/callback', methods=['POST', 'GET'])
def callback():
    data = json.loads(request.data)

    if request.method == 'GET':
        return 'I am alive!', 200

    if 'type' not in data:
        return 'not vk'

    if data['type'] == 'confirmation':
        return confirmation_token

    elif data['type'] == 'message_new':
        message = data['object']['message']['text']
        user_id = data['object']['message']['from_id']

        # Обработка состояний пользователя
        if user_id in user_state:
            state = user_state[user_id]
            
            if state['state'] == 'waiting_for_name':
                names = message.split()
                if len(names) >= 2:
                    user_data[user_id] = {
                        'first_name': names[1],
                        'last_name': names[0],
                        'birthdate': None,
                        'phone': None
                    }
                    user_state[user_id] = {'state': 'waiting_for_birthdate'}
                    send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", get_keyboard("get_birthdate", user_id))
                else:
                    send_message(user_id, "Пожалуйста, введите имя и фамилию через пробел (например: Иванов Иван)")
                return 'ok'
            
            elif state['state'] == 'waiting_for_birthdate':
                try:
                    datetime.strptime(message, '%d.%m.%Y')
                    user_data[user_id]['birthdate'] = message
                    user_state[user_id] = {'state': 'waiting_for_phone'}
                    send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                except ValueError:
                    send_message(user_id, "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
                return 'ok'
            
            elif state['state'] == 'waiting_for_phone':
                user_data[user_id]['phone'] = message
                # Сохраняем пользователя в таблицу
                register_user(
                    user_id,
                    user_data[user_id]['first_name'],
                    user_data[user_id]['last_name'],
                    user_data[user_id]['birthdate'],
                    user_data[user_id]['phone']
                )
                del user_state[user_id]
                send_message(user_id, "Спасибо за регистрацию!", get_keyboard("main"))
                return 'ok'
            
            elif state['state'] == 'waiting_for_question':
                send_message(user_id, "Подождите, скоро оператор свяжется с вами!", get_keyboard("null"))
                del user_state[user_id]
                return 'ok'
            
            elif state['state'] == 'selecting_club_date':
                try:
                    date = message.split(' (')[0]
                    datetime.strptime(date, '%d.%m.%Y')
                    user_state[user_id] = {
                        'state': 'selecting_club_time',
                        'club_id': state['club_id'],
                        'date': date
                    }
                    send_message(user_id, "Выберите время занятия:", 
                               get_club_times_keyboard(state['club_id'], date))
                except:
                    send_message(user_id, "Пожалуйста, выберите дату из предложенных вариантов")
                return 'ok'
            
            elif state['state'] == 'selecting_club_time':
                if ':' in message and len(message.split(':')) == 2:
                    user_state[user_id] = {
                        'state': 'confirming_club_registration',
                        'club_id': state['club_id'],
                        'date': state['date'],
                        'time': message
                    }
                    
                    club = next((c for c in get_active_clubs() if str(c['club_id']) == str(state['club_id'])), None)
                    if club:
                        response = (
                            "Проверьте вашу запись:\n\n"
                            f"Кружок: {club['name']}\n"
                            f"Дата: {state['date']}\n"
                            f"Время: {message}\n\n"
                            "Все верно?"
                        )
                        send_message(user_id, response, get_keyboard("confirm_registration"))
                else:
                    send_message(user_id, "Пожалуйста, выберите время из предложенных вариантов")
                return 'ok'
            
            elif state['state'] == 'confirming_club_registration':
                if message == "Подтверждаю":
                    success = register_for_club(
                        user_id,
                        state['club_id'],
                        state['date'],
                        state['time']
                    )
                    if success:
                        send_message(user_id, "Вы успешно записаны на кружок!", get_keyboard("main"))
                    else:
                        send_message(user_id, "Произошла ошибка при записи. Попробуйте позже.", get_keyboard("main"))
                    del user_state[user_id]
                elif message == "Не подтверждаю":
                    send_message(user_id, "Запись отменена", get_keyboard("main"))
                    del user_state[user_id]
                return 'ok'
            
            elif state['state'] == 'selecting_event':
                events = get_active_events()
                selected_event = next((e for e in events if e['name'] == message), None)
                if selected_event:
                    user_state[user_id] = {
                        'state': 'confirming_event_registration',
                        'event_id': selected_event['event_id']
                    }
                    response = (
                        f"{selected_event['name']}\n\n"
                        f"{selected_event['description']}\n\n"
                        f"Дата: {selected_event['date']}\n"
                        f"Время: {selected_event['time']}\n"
                        f"Место: {selected_event.get('location', 'Не указано')}\n\n"
                        "Хотите записаться?"
                    )
                    kb = VkKeyboard(one_time=False)
                    kb.add_button('Записаться!', color=VkKeyboardColor.POSITIVE)
                    kb.add_line()
                    kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
                    send_message(user_id, response, kb)
                return 'ok'
            
            elif state['state'] == 'confirming_event_registration':
                if message == "Записаться!":
                    success = register_for_event(user_id, state['event_id'])
                    if success:
                        send_message(user_id, "Спасибо за запись! Увидимся на мероприятии!", get_keyboard("main"))
                    else:
                        send_message(user_id, "Произошла ошибка при записи. Попробуйте позже.", get_keyboard("main"))
                    del user_state[user_id]
                elif message == "Назад":
                    send_message(user_id, "Выберите мероприятие:", get_keyboard("events"))
                    del user_state[user_id]
                return 'ok'

        # Обработка основных команд
        if message == "Начать":
            send_message(user_id, "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", get_keyboard("main"))
        
        elif message == "На главную":
            send_message(user_id, "Вот меню для получения информации:", get_keyboard("main"))
        
        elif message == "Личный кабинет":
            user = get_user_data(user_id)
            if user:
                send_message(user_id, "Выберите действие", get_keyboard("personal_account", user_id))
            else:
                send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", get_keyboard("personal_account", user_id))
        
        elif message == "Зарегистрироваться":
            user_state[user_id] = {'state': 'waiting_for_name'}
            send_message(user_id, "Прежде чем производить запись на кружок или мероприятие давайте зарегистрируемся! Ваши фамилия и имя(через пробел)?", get_keyboard("get_name", user_id))
        
        elif message == "Взять с профиля":
            if user_id in user_state:
                state = user_state[user_id]
                if state['state'] == 'waiting_for_name':
                    # В реальной реализации нужно получать данные из профиля VK
                    user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name,bdate')[0]
                    user_data[user_id] = {
                        'first_name': user_info.get('first_name', ''),
                        'last_name': user_info.get('last_name', ''),
                        'birthdate': None,
                        'phone': None
                    }
                    user_state[user_id] = {'state': 'waiting_for_birthdate'}
                    send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", get_keyboard("get_birthdate", user_id))
                elif state['state'] == 'waiting_for_birthdate':
                    user_info = vk.users.get(user_ids=user_id, fields='bdate')[0]
                    bdate = user_info.get('bdate', '')
                    if bdate:
                        try:
                            datetime.strptime(bdate, '%d.%m.%Y')
                            user_data[user_id]['birthdate'] = bdate
                            user_state[user_id] = {'state': 'waiting_for_phone'}
                            send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                        except:
                            send_message(user_id, "Не удалось получить дату рождения из профиля. Введите вручную (ДД.ММ.ГГГГ)")
                    else:
                        send_message(user_id, "Дата рождения не указана в профиле. Введите вручную (ДД.ММ.ГГГГ)")
                return 'ok'
        
        elif message == "Информация":
            user = get_user_data(user_id)
            if user:
                response = (
                    f"Ваши данные:\n"
                    f"Имя: {user.get('first_name', 'Не указано')}\n"
                    f"Фамилия: {user.get('last_name', 'Не указана')}\n"
                    f"Дата рождения: {user.get('birthdate', 'Не указана')}\n"
                    f"Телефон: {user.get('phone', 'Не указан')}"
                )
                send_message(user_id, response, get_keyboard("edit_info", user_id))
        
        elif message == "Мои записи":
            registrations = get_user_registrations(user_id)
            club_info = "Запись отсутствует"
            event_info = "Запись отсутствует"
            
            if registrations['club']:
                club = next((c for c in get_active_clubs() if str(c['club_id']) == str(registrations['club']['item_id'])), None)
                if club:
                    club_info = f"{club['name']}, {registrations['club']['date']} {registrations['club']['time']}"
            
            if registrations['event']:
                event = next((e for e in get_active_events() if str(e['event_id']) == str(registrations['event']['item_id'])), None)
                if event:
                    event_info = f"{event['name']}, {event['date']} {event['time']}"
            
            response = f"Ваши записи:\nКружок: {club_info}\nМероприятие: {event_info}"
            send_message(user_id, response, get_keyboard("personal_account", user_id))
        
        elif message == "Кружки и Мероприятия":
            send_message(user_id, "Выберите о чем хотите посмотреть информацию", get_keyboard("activities", user_id))
        
        elif message == "Кружок":
            if not get_user_data(user_id):
                send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", get_keyboard("personal_account", user_id))
            else:
                clubs = get_active_clubs()
                if not clubs:
                    send_message(user_id, "На данный момент нет доступных кружков", get_keyboard("activities", user_id))
                else:
                    send_message(user_id, "Выберите интересующее вас направление", get_keyboard("clubs", user_id))
        
        elif message in [club['name'] for club in get_active_clubs()]:
            club = next((c for c in get_active_clubs() if c['name'] == message), None)
            if club:
                user_state[user_id] = {
                    'state': 'selecting_club_date',
                    'club_id': club['club_id']
                }
                response = f"{club['name']}\n\n{club['description']}\n\nВыберите дату:"
                send_message(user_id, response, get_club_dates_keyboard(club['club_id']))
        
        elif message == "Мероприятие":
            events = get_active_events()
            if not events:
                send_message(user_id, "На данный момент запланированных мероприятий нет", get_keyboard("activities", user_id))
            elif len(events) == 1:
                event = events[0]
                user_state[user_id] = {
                    'state': 'confirming_event_registration',
                    'event_id': event['event_id']
                }
                response = (
                    f"{event['name']}\n\n"
                    f"{event['description']}\n\n"
                    f"Дата: {event['date']}\n"
                    f"Время: {event['time']}\n"
                    f"Место: {event.get('location', 'Не указано')}\n\n"
                    "Хотите записаться?"
                )
                kb = VkKeyboard(one_time=False)
                kb.add_button('Записаться!', color=VkKeyboardColor.POSITIVE)
                kb.add_line()
                kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
                send_message(user_id, response, kb)
            else:
                send_message(user_id, "Выберите интересующее вас мероприятие", get_keyboard("events", user_id))
        
        elif message in [event['name'] for event in get_active_events()]:
            event = next((e for e in get_active_events() if e['name'] == message), None)
            if event:
                user_state[user_id] = {
                    'state': 'confirming_event_registration',
                    'event_id': event['event_id']
                }
                response = (
                    f"{event['name']}\n\n"
                    f"{event['description']}\n\n"
                    f"Дата: {event['date']}\n"
                    f"Время: {event['time']}\n"
                    f"Место: {event.get('location', 'Не указано')}\n\n"
                    "Хотите записаться?"
                )
                kb = VkKeyboard(one_time=False)
                kb.add_button('Записаться!', color=VkKeyboardColor.POSITIVE)
                kb.add_line()
                kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
                send_message(user_id, response, kb)
        
        elif message == "Вопросы":
            send_message(user_id, "Есть вопросы?", get_keyboard("questions", user_id))
        
        elif message == "Часто задаваемые вопросы":
            faqs = faq_sheet.get_all_records()
            if not faqs:
                send_message(user_id, "Пока нет часто задаваемых вопросов", get_keyboard("questions", user_id))
            else:
                send_message(user_id, "Возможно вам нужен ответ на один из этих вопросов", get_keyboard("faq", user_id))
        
        elif message in [faq['question'] for faq in faq_sheet.get_all_records()]:
            faq = next((f for f in faq_sheet.get_all_records() if f['question'] == message), None)
            if faq:
                send_message(user_id, f"Q: {faq['question']}\nA: {faq['answer']}", get_keyboard("faq", user_id))
        
        elif message == "Свой вопрос":
            user_state[user_id] = {'state': 'waiting_for_question'}
            send_message(user_id, "Введите свой вопрос", get_keyboard("null"))
        
        elif message == "Назад":
            send_message(user_id, "Возвращаемся назад", get_keyboard("main"))

        return 'ok'

    return 'unsupported'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
