from flask import Flask, request
import json
import random
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

app = Flask(__name__)

confirmation_token = 'c9d9ac77'
token = 'vk1.a.69EGRWB1sbkT5O5nNF5WLcI9rsjx9_gDHPEcWWAQvL26fMZVkzKmoHM4fBNQMGjLhkQDAD-0NU16OALmxM_HmsyF0gDykLWuIjU1YV5ZlyWqQZD_r_8qTKp8NYsH8-04_9d9q1UA6IvBbj4_qd8a5o_F4Fr75eSGKWyw0x1kt1XfhW_W3GEaEC_u2Nt2lcH7kv7qo8wdQatf6BzohS5asA'


vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

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
        if user_id in user_data:
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
        # Заглушка - в реальности брать из БД
        kb.add_button('Программирование')
        kb.add_line()
        kb.add_button('Дизайн')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "club_dates":
        # Заглушка - в реальности брать из БД
        kb.add_button('15.05.2023 (пн)')
        kb.add_line()
        kb.add_button('17.05.2023 (ср)')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "club_times":
        # Заглушка - в реальности брать из БД
        kb.add_button('15:00')
        kb.add_line()
        kb.add_button('17:00')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "confirm_registration":
        kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Не подтверждаю', color=VkKeyboardColor.NEGATIVE)

    elif name == "events":
        # Заглушка - в реальности проверять наличие мероприятий в БД
        kb.add_button('Концерт')
        kb.add_line()
        kb.add_button('Мастер-класс')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "questions":
        kb.add_button('Часто задаваемые вопросы')
        kb.add_line()
        kb.add_button('Свой вопрос')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "faq":
        # Заглушка - в реальности брать из БД
        kb.add_button('Как записаться?')
        kb.add_line()
        kb.add_button('Где проходят занятия?')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    return kb

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
                del user_state[user_id]
                send_message(user_id, "Спасибо за регистрацию!", get_keyboard("main"))
                return 'ok'
            
            elif state['state'] == 'waiting_for_question':
                send_message(user_id, "Подождите, скоро оператор свяжется с вами!", get_keyboard("null"))
                del user_state[user_id]
                return 'ok'

        # Обработка основных команд
        if message == "Начать":
            send_message(user_id, "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", get_keyboard("main"))
        
        elif message == "На главную":
            send_message(user_id, "Вот меню для получения информации:", get_keyboard("main"))
        
        elif message == "Личный кабинет":
            if user_id in user_data:
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
                    # В реальности нужно получить данные из профиля VK
                    user_data[user_id] = {
                        'first_name': 'Иван',  # Заглушка
                        'last_name': 'Иванов',  # Заглушка
                        'birthdate': None,
                        'phone': None
                    }
                    user_state[user_id] = {'state': 'waiting_for_birthdate'}
                    send_message(user_id, "Ваша дата рождения? (формат: ДД.ММ.ГГГГ)", get_keyboard("get_birthdate", user_id))
                elif state['state'] == 'waiting_for_birthdate':
                    # В реальности нужно получить данные из профиля VK
                    user_data[user_id]['birthdate'] = '01.01.2000'  # Заглушка
                    user_state[user_id] = {'state': 'waiting_for_phone'}
                    send_message(user_id, "Ваш номер телефона?", get_keyboard("null"))
        
        elif message == "Информация":
            if user_id in user_data:
                user = user_data[user_id]
                response = f"Ваши данные:\nИмя: {user['first_name']}\nФамилия: {user['last_name']}\nДата рождения: {user['birthdate']}\nТелефон: {user['phone']}"
                send_message(user_id, response, get_keyboard("edit_info", user_id))
        
        elif message == "Мои записи":
            if user_id in user_data:
                if user_id in user_registrations:
                    registrations = user_registrations[user_id]
                    club_info = registrations.get('club', 'Запись отсутствует')
                    event_info = registrations.get('event', 'Запись отсутствует')
                    response = f"Ваши записи:\nКружок: {club_info}\nМероприятие: {event_info}"
                else:
                    response = "Ваши записи:\nКружок: Запись отсутствует\nМероприятие: Запись отсутствует"
                send_message(user_id, response, get_keyboard("personal_account", user_id))
        
        elif message == "Кружки и Мероприятия":
            send_message(user_id, "Выберите о чем хотите посмотреть информацию", get_keyboard("activities", user_id))
        
        elif message == "Кружок":
            if user_id not in user_data:
                send_message(user_id, "У вас отсутствует личный кабинет! Зарегистрируйте его!", get_keyboard("personal_account", user_id))
            else:
                send_message(user_id, "Выберите интересующее вас направление", get_keyboard("clubs", user_id))
        
        elif message in ["Программирование", "Дизайн"]:  # Заглушки для кружков
            send_message(user_id, f"{message}: описание кружка, выберите дату", get_keyboard("club_dates", user_id))
        
        elif message in ["15.05.2023 (пн)", "17.05.2023 (ср)"]:  # Заглушки для дат
            send_message(user_id, "Выберите время занятия", get_keyboard("club_times", user_id))
        
        elif message in ["15:00", "17:00"]:  # Заглушки для времени
            # В реальности нужно сохранить запись в БД
            if user_id not in user_registrations:
                user_registrations[user_id] = {}
            user_registrations[user_id]['club'] = f"Программирование, {message}"  # Заглушка
            send_message(user_id, f"Проверьте вашу запись:\nКружок: Программирование\nВремя: {message}", get_keyboard("confirm_registration", user_id))
        
        elif message == "Подтверждаю":
            send_message(user_id, "Вы успешно записаны на кружок!", get_keyboard("main"))
        
        elif message == "Не подтверждаю":
            send_message(user_id, "Спасибо за ваше время!", get_keyboard("main"))
        
        elif message == "Мероприятие":
            # В реальности проверять наличие мероприятий в БД
            send_message(user_id, "Выберите интересующее вас мероприятие", get_keyboard("events", user_id))
        
        elif message in ["Концерт", "Мастер-класс"]:  # Заглушки для мероприятий
            # В реальности брать данные из БД
            send_message(user_id, f"{message}: описание мероприятия\nДата: 20.05.2023\nВремя: 18:00", get_keyboard("confirm_registration", user_id))
        
        elif message == "Записаться!":
            # В реальности сохранять запись в БД
            if user_id not in user_registrations:
                user_registrations[user_id] = {}
            user_registrations[user_id]['event'] = "Концерт, 20.05.2023, 18:00"  # Заглушка
            send_message(user_id, "Спасибо за запись! Увидимся на мероприятии!", get_keyboard("main"))
        
        elif message == "Вопросы":
            send_message(user_id, "Есть вопросы?", get_keyboard("questions", user_id))
        
        elif message == "Часто задаваемые вопросы":
            send_message(user_id, "Возможно вам нужен ответ на один из этих вопросов", get_keyboard("faq", user_id))
        
        elif message in ["Как записаться?", "Где проходят занятия?"]:  # Заглушки для FAQ
            send_message(user_id, f"Q: {message}\nA: Ответ на вопрос '{message}'", get_keyboard("faq", user_id))
        
        elif message == "Свой вопрос":
            user_state[user_id] = {'state': 'waiting_for_question'}
            send_message(user_id, "Введите свой вопрос", get_keyboard("null"))
        
        elif message == "Назад":
            # Обработка кнопки "Назад" в зависимости от контекста
            # В реальности нужно отслеживать предыдущее состояние пользователя
            send_message(user_id, "Возвращаемся назад", get_keyboard("main"))

        return 'ok'

    return 'unsupported'

def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.getrandbits(64),
        keyboard=keyboard.get_keyboard() if keyboard else None
    )


