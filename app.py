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

def get_keyboard(name):
    kb = VkKeyboard(one_time=False)

    if name == "null":
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "main":
        kb.add_button('Расписание')
        kb.add_line()
        kb.add_button('Частые вопросы')
        kb.add_line()
        kb.add_button('Свой вопрос')
        kb.add_line()
        kb.add_button('Напоминания')

    elif name == "schedule":
        kb.add_button('Неделя')
        kb.add_line()
        kb.add_button('Кружок')
        kb.add_line()
        kb.add_button('Мероприятия')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "class":
        kb.add_button('Время')
        kb.add_line()
        kb.add_button('Запомнить')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "questions":
        kb.add_button('Категория')
        kb.add_line()
        kb.add_button('Свой вопрос')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "topic":
        kb.add_button('Вопрос')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    return kb

@app.route('/callback', methods=['POST'])
def callback():
    data = json.loads(request.data)

    if 'type' not in data:
        return 'not vk'

    if data['type'] == 'confirmation':
        return confirmation_token

    elif data['type'] == 'message_new':
        message = data['object']['message']['text']
        user_id = data['object']['message']['from_id']

        if message == "Начать":
            send_message(user_id, "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта».", get_keyboard("null"))
        elif message == "На главную":
            send_message(user_id, "Вот меню для получения информации:", get_keyboard("main"))
        elif message == "Расписание" or message == "Назад":
            send_message(user_id, "Вот информация про события на эту неделю.", get_keyboard("schedule"))
        elif message == "Кружок":
            send_message(user_id, "(Информация про кружок)", get_keyboard("class"))
        elif message == "Частые вопросы":
            send_message(user_id, "Что вы хотите узнать?", get_keyboard("questions"))
        elif message == "Категория":
            send_message(user_id, "Список вопросов этой категории:", get_keyboard("topic"))
        elif message == "Вопрос":
            send_message(user_id, "(Ответ)", get_keyboard("topic"))
        elif message == "Свой вопрос":
            send_message(user_id, "Оператор ответит вам в течение Х времени, ожидайте.", get_keyboard("null"))

        return 'ok'

    return 'unsupported'

def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.getrandbits(64),
        keyboard=keyboard.get_keyboard() if keyboard else None
    )

