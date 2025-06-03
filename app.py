from flask import Flask, request
import json
import random
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date, time
import os
from settings import confirmation_token, token

app = Flask(__name__)

# Конфигурация базы данных alwaysdata.com
db_config = {
    'host': 'mysql-ostrova.alwaysdata.net',
    'database': 'ostrova_ostrova_base',
    'user': 'ostrova',
    'password': os.getenv('DB_PASSWORD')  # Пароль из переменных окружения
}

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

# Глобальный словарь для хранения состояний пользователей
user_state = {}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Ошибка подключения к MySQL: {e}")
        return None

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
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            connection.close()
            
            if user:
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
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Clubs WHERE active = TRUE")
            clubs = cursor.fetchall()
            connection.close()
            
            for club in clubs:
                kb.add_button(club['name'])
                kb.add_line()
            kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "club_dates":
        if 'club_id' in user_state.get(user_id, {}):
            club_id = user_state[user_id]['club_id']
            connection = create_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT DISTINCT date, DAYNAME(date) as day_of_week 
                    FROM Club_Schedule 
                    WHERE club_id = %s AND date >= CURDATE()
                    ORDER BY date
                    LIMIT 5
                """, (club_id,))
                dates = cursor.fetchall()
                connection.close()
                
                for d in dates:
                    formatted_date = d['date'].strftime('%d.%m.%Y')
                    kb.add_button(f"{formatted_date} ({d['day_of_week']})")
                    kb.add_line()
                kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "club_times":
        if 'club_id' in user_state.get(user_id, {}) and 'selected_date' in user_state.get(user_id, {}):
            club_id = user_state[user_id]['club_id']
            selected_date = user_state[user_id]['selected_date']
            
            connection = create_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT schedule_id, start_time, end_time, max_participants, current_participants
                    FROM Club_Schedule
                    WHERE club_id = %s AND date = %s AND current_participants < max_participants
                    ORDER BY start_time
                """, (club_id, selected_date))
                times = cursor.fetchall()
                connection.close()
                
                for t in times:
                    start_time = t['start_time'].strftime('%H:%M')
                    end_time = t['end_time'].strftime('%H:%M')
                    kb.add_button(f"{start_time}-{end_time} ({t['current_participants']}/{t['max_participants']})")
                    kb.add_line()
                    if 'schedule_choices' not in user_state[user_id]:
                        user_state[user_id]['schedule_choices'] = {}
                    user_state[user_id]['schedule_choices'][f"{start_time}-{end_time}"] = t['schedule_id']
                kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "confirm_registration":
        kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Не подтверждаю', color=VkKeyboardColor.NEGATIVE)

    elif name == "events":
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM Events 
                WHERE active = TRUE AND date >= CURDATE()
                ORDER BY date, time
            """)
            events = cursor.fetchall()
            connection.close()
            
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
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM FAQ")
            faqs = cursor.fetchall()
            connection.close()
            
            for faq in faqs:
                kb.add_button(faq['question'])
                kb.add_line()
            kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    return kb

def send_message(user_id, message, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.getrandbits(64),
            keyboard=keyboard.get_keyboard() if keyboard else None
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

@app.route('/callback', methods=['POST', 'GET'])
def callback():
    if request.method == 'GET':
        return 'I am alive!', 200

    try:
        data = json.loads(request.data)
    except json.JSONDecodeError:
        return 'Invalid JSON', 400

    if 'type' not in data:
        return 'not vk', 400

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
                    connection = create_db_connection()
                    if connection:
                        try:
                            cursor = connection.cursor()
                            cursor.execute("""
                                INSERT INTO Users (user_id, first_name, last_name, reg_date)
                                VALUES (%s, %s, %s, CURDATE())
                                ON DUPLICATE KEY UPDATE first_name = %s, last_name = %s
                            """, (user_id, names[1], names[0], names[1], names[0]))
                            connection.commit()
                            user_state[user_id] = {'state': 'waiting_for_birthdate'}
                            send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", get_keyboard("get_birthdate", user_id))
                        except Error as e:
                            print(f"Ошибка БД: {e}")
                            send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                        finally:
                            connection.close()
                else:
                    send_message(user_id, "Пожалуйста, введите имя и фамилию через пробел (например: Иванов Иван)")
                return 'ok'
            
            elif state['state'] == 'waiting_for_birthdate':
                try:
                    birthdate = datetime.strptime(message, '%d.%m.%Y').date()
                    connection = create_db_connection()
                    if connection:
                        try:
                            cursor = connection.cursor()
                            cursor.execute("""
                                UPDATE Users SET birthdate = %s WHERE user_id = %s
                            """, (birthdate, user_id))
                            connection.commit()
                            user_state[user_id] = {'state': 'waiting_for_phone'}
                            send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                        except Error as e:
                            print(f"Ошибка БД: {e}")
                            send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                        finally:
                            connection.close()
                except ValueError:
                    send_message(user_id, "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
                return 'ok'
            
            elif state['state'] == 'waiting_for_phone':
                connection = create_db_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("""
                            UPDATE Users SET phone = %s WHERE user_id = %s
                        """, (message, user_id))
                        connection.commit()
                        del user_state[user_id]
                        send_message(user_id, "Спасибо за регистрацию!", get_keyboard("main"))
                    except Error as e:
                        print(f"Ошибка БД: {e}")
                        send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                    finally:
                        connection.close()
                return 'ok'
            
            elif state['state'] == 'waiting_for_question':
                send_message(user_id, "Подождите, скоро оператор свяжется с вами!", get_keyboard("null"))
                del user_state[user_id]
                return 'ok'

            elif state['state'] == 'choosing_club_date':
                try:
                    date_part = message.split()[0]
                    selected_date = datetime.strptime(date_part, '%d.%m.%Y').date()
                    user_state[user_id]['selected_date'] = selected_date
                    user_state[user_id]['state'] = 'choosing_club_time'
                    send_message(user_id, "Выберите время занятия", get_keyboard("club_times", user_id))
                except ValueError:
                    send_message(user_id, "Пожалуйста, выберите дату из предложенных вариантов")
                return 'ok'

            elif state['state'] == 'choosing_club_time':
                if 'schedule_choices' in user_state[user_id]:
                    time_slot = message.split()[0]
                    schedule_id = user_state[user_id]['schedule_choices'].get(time_slot)
                    if schedule_id:
                        user_state[user_id]['schedule_id'] = schedule_id
                        user_state[user_id]['state'] = 'confirming_club_registration'
                        
                        connection = create_db_connection()
                        if connection:
                            try:
                                cursor = connection.cursor(dictionary=True)
                                cursor.execute("""
                                    SELECT c.name, cs.date, cs.start_time, cs.end_time 
                                    FROM Club_Schedule cs
                                    JOIN Clubs c ON cs.club_id = c.club_id
                                    WHERE cs.schedule_id = %s
                                """, (schedule_id,))
                                schedule = cursor.fetchone()
                                
                                if schedule:
                                    response = f"Проверьте вашу запись:\nКружок: {schedule['name']}\n"
                                    response += f"Дата: {schedule['date'].strftime('%d.%m.%Y')}\n"
                                    response += f"Время: {schedule['start_time'].strftime('%H:%M')}-{schedule['end_time'].strftime('%H:%M')}"
                                    send_message(user_id, response, get_keyboard("confirm_registration", user_id))
                            except Error as e:
                                print(f"Ошибка БД: {e}")
                                send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                            finally:
                                connection.close()
                return 'ok'

            elif state['state'] == 'confirming_club_registration' and message == "Подтверждаю":
                if 'schedule_id' in user_state[user_id]:
                    schedule_id = user_state[user_id]['schedule_id']
                    connection = create_db_connection()
                    if connection:
                        try:
                            connection.start_transaction()
                            cursor = connection.cursor()
                            
                            # Проверяем, не записан ли уже пользователь
                            cursor.execute("""
                                SELECT * FROM Registrations 
                                WHERE user_id = %s AND type = 'club' AND item_id = %s AND status = 'active'
                            """, (user_id, schedule_id))
                            if cursor.fetchone():
                                send_message(user_id, "Вы уже записаны на это занятие!", get_keyboard("main"))
                            else:
                                # Записываем пользователя
                                cursor.execute("""
                                    INSERT INTO Registrations 
                                    (user_id, type, item_id, date, time, status) 
                                    VALUES (%s, 'club', %s, CURDATE(), CURTIME(), 'active')
                                """, (user_id, schedule_id))
                                
                                # Увеличиваем счетчик участников
                                cursor.execute("""
                                    UPDATE Club_Schedule 
                                    SET current_participants = current_participants + 1 
                                    WHERE schedule_id = %s
                                """, (schedule_id,))
                                
                                connection.commit()
                                
                                # Получаем информацию о записи для подтверждения
                                cursor.execute("""
                                    SELECT c.name, cs.date, cs.start_time, cs.end_time 
                                    FROM Club_Schedule cs
                                    JOIN Clubs c ON cs.club_id = c.club_id
                                    WHERE cs.schedule_id = %s
                                """, (schedule_id,))
                                schedule = cursor.fetchone()
                                
                                send_message(user_id, f"Вы успешно записаны на {schedule['name']} {schedule['date'].strftime('%d.%m.%Y')} {schedule['start_time'].strftime('%H:%M')}-{schedule['end_time'].strftime('%H:%M')}!", get_keyboard("main"))
                        except Error as e:
                            connection.rollback()
                            print(f"Ошибка транзакции: {e}")
                            send_message(user_id, "Произошла ошибка при записи. Пожалуйста, попробуйте позже.", get_keyboard("main"))
                        finally:
                            connection.close()
                
                if user_id in user_state:
                    del user_state[user_id]
                return 'ok'

        # Обработка основных команд
        if message == "Начать":
            send_message(user_id, "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", get_keyboard("main"))
        
        elif message == "На главную":
            send_message(user_id, "Вот меню для получения информации:", get_keyboard("main"))
        
        elif message == "Личный кабинет":
            send_message(user_id, "Выберите действие", get_keyboard("personal_account", user_id))
        
        elif message == "Зарегистрироваться":
            user_state[user_id] = {'state': 'waiting_for_name'}
            send_message(user_id, "Прежде чем производить запись на кружок или мероприятие давайте зарегистрируемся! Ваши фамилия и имя(через пробел)?", get_keyboard("get_name", user_id))
        
        elif message == "Взять с профиля":
            if user_id in user_state:
                state = user_state[user_id]
                if state['state'] == 'waiting_for_name':
                    try:
                        user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name')[0]
                        first_name = user_info.get('first_name', '')
                        last_name = user_info.get('last_name', '')
                        
                        connection = create_db_connection()
                        if connection:
                            try:
                                cursor = connection.cursor()
                                cursor.execute("""
                                    INSERT INTO Users (user_id, first_name, last_name, reg_date)
                                    VALUES (%s, %s, %s, CURDATE())
                                    ON DUPLICATE KEY UPDATE first_name = %s, last_name = %s
                                """, (user_id, first_name, last_name, first_name, last_name))
                                connection.commit()
                                user_state[user_id] = {'state': 'waiting_for_birthdate'}
                                send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", get_keyboard("get_birthdate", user_id))
                            except Error as e:
                                print(f"Ошибка БД: {e}")
                                send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                            finally:
                                connection.close()
                    except Exception as e:
                        print(f"Ошибка VK API: {e}")
                        send_message(user_id, "Не удалось получить данные из профиля. Введите имя и фамилию вручную.")
                
                elif state['state'] == 'waiting_for_birthdate':
                    try:
                        user_info = vk.users.get(user_ids=user_id, fields='bdate')[0]
                        bdate = user_info.get('bdate', '')
                        if bdate:
                            try:
                                birthdate = datetime.strptime(bdate, '%d.%m.%Y').date()
                                connection = create_db_connection()
                                if connection:
                                    try:
                                        cursor = connection.cursor()
                                        cursor.execute("""
                                            UPDATE Users SET birthdate = %s WHERE user_id = %s
                                        """, (birthdate, user_id))
                                        connection.commit()
                                        user_state[user_id] = {'state': 'waiting_for_phone'}
                                        send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
                                    except Error as e:
                                        print(f"Ошибка БД: {e}")
                                        send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                                    finally:
                                        connection.close()
                            except ValueError:
                                send_message(user_id, "Не удалось распознать дату рождения из профиля. Введите вручную в формате ДД.ММ.ГГГГ")
                        else:
                            send_message(user_id, "Дата рождения не указана в профиле. Введите вручную в формате ДД.ММ.ГГГГ")
                    except Exception as e:
                        print(f"Ошибка VK API: {e}")
                        send_message(user_id, "Не удалось получить данные из профиля. Введите дату рождения вручную.")
        
        elif message == "Информация":
            connection = create_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
                    user = cursor.fetchone()
                    
                    if user:
                        response = f"Ваши данные:\nИмя: {user.get('first_name', 'не указано')}\nФамилия: {user.get('last_name', 'не указано')}\n"
                        response += f"Дата рождения: {user['birthdate'].strftime('%d.%m.%Y') if user.get('birthdate') else 'не указана'}\n"
                        response += f"Телефон: {user.get('phone', 'не указан')}"
                        send_message(user_id, response, get_keyboard("edit_info", user_id))
                    else:
                        send_message(user_id, "Вы не зарегистрированы!", get_keyboard("personal_account", user_id))
                except Error as e:
                    print(f"Ошибка БД: {e}")
                    send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                finally:
                    connection.close()
        
        elif message == "Мои записи":
            connection = create_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    
                    # Получаем записи на кружки
                    cursor.execute("""
                        SELECT c.name, cs.date, cs.start_time, cs.end_time 
                        FROM Registrations r
                        JOIN Club_Schedule cs ON r.item_id = cs.schedule_id
                        JOIN Clubs c ON cs.club_id = c.club_id
                        WHERE r.user_id = %s AND r.type = 'club' AND r.status = 'active'
                    """, (user_id,))
                    club_regs = cursor.fetchall()
                    
                    # Получаем записи на мероприятия
                    cursor.execute("""
                        SELECT e.name, e.date, e.time, e.location 
                        FROM Registrations r
                        JOIN Events e ON r.item_id = e.event_id
                        WHERE r.user_id = %s AND r.type = 'event' AND r.status = 'active'
                    """, (user_id,))
                    event_regs = cursor.fetchall()
                    
                    response = "Ваши записи:\n\n"
                    response += "Кружки:\n"
                    if club_regs:
                        for reg in club_regs:
                            response += f"- {reg['name']} {reg['date'].strftime('%d.%m.%Y')} {reg['start_time'].strftime('%H:%M')}-{reg['end_time'].strftime('%H:%M')}\n"
                    else:
                        response += "Нет записей\n"
                    
                    response += "\nМероприятия:\n"
                    if event_regs:
                        for reg in event_regs:
                            response += f"- {reg['name']} {reg['date'].strftime('%d.%m.%Y')} {reg['time'].strftime('%H:%M')} ({reg['location']})\n"
                    else:
                        response += "Нет записей\n"
                    
                    send_message(user_id, response, get_keyboard("personal_account", user_id))
                except Error as e:
                    print(f"Ошибка БД: {e}")
                    send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                finally:
                    connection.close()
        
        elif message == "Кружки и Мероприятия":
            send_message(user_id, "Выберите о чем хотите посмотреть информацию", get_keyboard("activities", user_id))
        
        elif message == "Кружок":
            connection = create_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
                    user = cursor.fetchone()
                    
                    if not user:
                        send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", get_keyboard("personal_account", user_id))
                    else:
                        send_message(user_id, "Выберите интересующее вас направление", get_keyboard("clubs", user_id))
                except Error as e:
                    print(f"Ошибка БД: {e}")
                    send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                finally:
                    connection.close()
        
        elif message in ["Круговая тренировка", "Занятие по английскому языку (Beginner)", "Мастерская рукоделия \"Путь творчества\"", 
                        "Клуб \"Есть выбор\"", "Кружок начинающих гитаристов (по предварительной записи)", 
                        "Занятие по английскому языку (Pre-Intermediate)", "Занятие по английскому языку (Elementary)", 
                        "Занятие по английскому языку (Pre-Intermediate+)", "Игротека", 
                        "Стретчинг всех мышечных групп (по предварительной записи)", "Электроника и программирование", 
                        "Психологическая мастерская", "Сплит тренировка"]:
            connection = create_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT club_id FROM Clubs WHERE name = %s", (message,))
                    club = cursor.fetchone()
                    
                    if club:
                        user_state[user_id] = {
                            'state': 'choosing_club_date',
                            'club_id': club['club_id']
                        }
                        send_message(user_id, f"{message}: выберите дату", get_keyboard("club_dates", user_id))
                except Error as e:
                    print(f"Ошибка БД: {e}")
                    send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                finally:
                    connection.close()
        
        elif message == "Мероприятие":
            send_message(user_id, "Выберите интересующее вас мероприятие", get_keyboard("events", user_id))
        
        elif message == "Вопросы":
            send_message(user_id, "Есть вопросы?", get_keyboard("questions", user_id))
        
        elif message == "Часто задаваемые вопросы":
            send_message(user_id, "Возможно вам нужен ответ на один из этих вопросов", get_keyboard("faq", user_id))
        
        elif message == "Свой вопрос":
            user_state[user_id] = {'state': 'waiting_for_question'}
            send_message(user_id, "Введите свой вопрос", get_keyboard("null"))
        
        elif message == "Назад":
            send_message(user_id, "Возвращаемся назад", get_keyboard("main"))
        
        else:
            # Проверяем, является ли сообщение вопросом из FAQ
            connection = create_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT answer FROM FAQ WHERE question = %s", (message,))
                    faq = cursor.fetchone()
                    
                    if faq:
                        send_message(user_id, faq['answer'], get_keyboard("faq", user_id))
                    else:
                        send_message(user_id, "Не понимаю вашего сообщения. Пожалуйста, используйте кнопки.", get_keyboard("main"))
                except Error as e:
                    print(f"Ошибка БД: {e}")
                    send_message(user_id, "Произошла ошибка. Попробуйте позже.", get_keyboard("main"))
                finally:
                    connection.close()

        return 'ok'

    return 'unsupported'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
