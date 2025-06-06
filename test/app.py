from flask import Flask, request
import json
import random
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import datetime
import db
import keyboards

app = Flask(__name__)

# Токены и API
confirmation_token = 'c9d9ac77'
token = 'vk1.a.69EGRWB1sbkT5O5nNF5WLcI9rsjx9_gDHPEcWWAQvL26fMZVkzKmoHM4fBNQMGjLhkQDAD-0NU16OALmxM_HmsyF0gDykLWuIjU1YV5ZlyWqQZD_r_8qTKp8NYsH8-04_9d9q1UA6IvBbj4_qd8a5o_F4Fr75eSGKWyw0x1kt1XfhW_W3GEaEC_u2Nt2lcH7kv7qo8wdQatf6BzohS5asA'
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

# Глобальные словари для хранения состояний
user_state = {}
user_registrations = {}

def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.getrandbits(64),
        keyboard=keyboardboards.get_keyboard(keyboard) if keyboard else None
    )

@app.route('/callback', methods=['POST', 'GET'])
def callback():
    data = request.json
    if not data:
        return 'not vk', 400

    if data['type'] == 'confirmation':
        return confirmation_token

    elif data['type'] == 'message_new':
        obj = data['object']['message']
        user_id = obj['from_id']
        message = obj['text'].strip()

        # Обработка состояний пользователя
        if user_id in user_state:
            state = user_state[user_id]

            if state == 'waiting_for_name':
                names = message.split()
                if len(names) >= 2:
                    db.save_user_to_db(user_id, names[1], names[0])
                    user_state[user_id] = 'waiting_for_birthdate'
                    send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", "get_birthdate")
                else:
                    send_message(user_id, "Пожалуйста, введите имя и фамилию через пробел", "null")
                return 'ok'

            elif state == 'waiting_for_birthdate':
                try:
                    datetime.strptime(message, '%d.%m.%Y')
                    db.update_user_field(user_id, 'birthdate', message)
                    user_state[user_id] = 'waiting_for_phone'
                    send_message(user_id, "Ваш номер телефона?", "null")
                except ValueError:
                    send_message(user_id, "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                return 'ok'

            elif state == 'waiting_for_phone':
                db.update_user_field(user_id, 'phone', message)
                del user_state[user_id]
                send_message(user_id, "Спасибо за регистрацию!", "main")
                return 'ok'

            elif state == 'waiting_for_question':
                send_message(user_id, "Подождите, скоро оператор свяжется с вами!", "null")
                del user_state[user_id]
                return 'ok'

        # Основное меню
        if message == "Начать":
            send_message(user_id, "Приветственный текст", "main")

        elif message == "Личный кабинет":
            if db.user_exists_in_db(user_id):
                send_message(user_id, "Выберите действие", "personal_account")
            else:
                send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", "personal_account")

        elif message == "Зарегистрироваться":
            user_state[user_id] = 'waiting_for_name'
            send_message(user_id, "Прежде чем производить запись на кружок или мероприятие давайте зарегистрируемся! Ваши фамилия и имя(через пробел)?", "get_name")

        elif message == "Взять с профиля":
            if user_id in user_state:
                if user_state[user_id] == 'waiting_for_name':
                    # Здесь можно получить данные из VK через метод users.get
                    db.save_user_to_db(user_id, "Иван", "Иванов")
                    user_state[user_id] = 'waiting_for_birthdate'
                    send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", "get_birthdate")

        elif message == "На главную":
            send_message(user_id, "Главное меню", "main")

        elif message == "Кружки и Мероприятия":
            if not db.user_exists_in_db(user_id):
                send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", "personal_account")
            else:
                send_message(user_id, "Выберите о чем хотите посмотреть информацию", "activities")

        elif message == "Вопросы":
            send_message(user_id, "Есть вопросы?", "questions")

        elif message == "Часто задаваемые вопросы":
            questions = db.get_all_faq()
            kb = keyboards.generate_faq_buttons()
            for q in questions:
                kb.add_button(q[1])
            kb.add_line()
            kb.add_button("Назад", color=VkKeyboardColor.PRIMARY)
            send_message(user_id, "Возможно вам нужен ответ на один из этих вопросов", kb)

        elif message == "Свой вопрос":
            user_state[user_id] = 'waiting_for_question'
            send_message(user_id, "Введите свой вопрос", "null")

        elif message == "Информация":
            info = db.get_user_info(user_id)
            send_message(user_id, f"Имя: {info[0]}\nФамилия: {info[1]}\nДата рождения: {info[2]}\nТелефон: {info[3]}", "edit_info")

        elif message == "Редактировать информацию":
            send_message(user_id, "Какие данные хотите изменить?", "edit_info")

        elif message == "Имя и Фамилия":
            user_state[user_id] = 'waiting_for_name'
            send_message(user_id, "Введите новое имя и фамилию", "get_name")

        elif message == "Дата рождения":
            user_state[user_id] = 'waiting_for_birthdate'
            send_message(user_id, "Введите новую дату рождения", "get_birthdate")

        elif message == "Номер телефона":
            user_state[user_id] = 'waiting_for_phone'
            send_message(user_id, "Введите новый номер телефона", "null")

        elif message == "Кружок":
            clubs = db.get_all_clubs()
            kb = keyboards.empty_kb()
            for club in clubs:
                kb.add_button(club[1])
            kb.add_line()
            kb.add_button("Назад", color=VkKeyboardColor.PRIMARY)
            send_message(user_id, "Выберите интересующее вас направление", kb)

        elif message == "Мероприятие":
            events = db.get_all_events()
            if not events:
                send_message(user_id, "На данный момент запланированных мероприятий нет", "events_back")
            elif len(events) == 1:
                event = events[0]
                send_message(user_id, f"{event[1]}\n\n{event[2]}\nДата: {event[3]}, Время: {event[4]}\nМесто: {event[5]}", "register_event")
            else:
                kb = keyboards.empty_kb()
                for event in events:
                    kb.add_button(event[1])
                kb.add_line()
                kb.add_button("Назад", color=VkKeyboardColor.PRIMARY)
                send_message(user_id, "Выберите интересующее вас мероприятие", kb)

        elif message == "Записаться!":
            event_id = 1  # Пример ID события
            db.register_for_item(user_id, 'event', event_id)
            send_message(user_id, "Спасибо за запись! Увидимся на мероприятии!", "main")

    return 'ok'
