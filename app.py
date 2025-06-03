from flask import Flask, request
import json
import random
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import mysql.connector
from datetime import datetime
from settings import confirmation_token, token

app = Flask(__name__)

# Подключение к БД (добавлено)
def get_db():
    try:
        return mysql.connector.connect(
            host="mysql-ostrova.alwaysdata.net",
            user="ostrova",
            password="your_password",  # Замените на реальный
            database="ostrova_ostrova_base"
        )
    except Exception as e:
        print("Ошибка подключения к БД:", e)
        return None

# Оригинальные глобальные переменные
user_state = {}
user_data = {}
user_registrations = {}

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

# Оригинальная функция get_keyboard без изменений
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
    # ... (остальное как в оригинале) ...
    return kb

# Новая функция для сохранения в БД
def save_to_db(user_id, data):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Users (user_id, first_name, last_name, birthdate, phone, reg_date)
                VALUES (%s, %s, %s, %s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                birthdate = VALUES(birthdate),
                phone = VALUES(phone)
            """, (user_id, data['first_name'], data['last_name'], data['birthdate'], data['phone']))
            conn.commit()
        except Exception as e:
            print("Ошибка сохранения в БД:", e)
        finally:
            conn.close()

@app.route('/callback', methods=['POST'])
def callback():
    data = json.loads(request.data)

    if data['type'] == 'confirmation':
        return confirmation_token

    if data['type'] == 'message_new':
        message = data['object']['message']['text']
        user_id = data['object']['message']['from_id']

        # Оригинальная логика обработки сообщений
        if message == "Начать":
            send_message(user_id, "Приветствуем в клубе!", get_keyboard("main"))
        
        elif message == "Зарегистрироваться":
            user_state[user_id] = {'state': 'waiting_for_name'}
            send_message(user_id, "Введите имя и фамилию:", get_keyboard("null"))

        # ... (вся остальная оригинальная логика) ...

        elif user_id in user_state and user_state[user_id]['state'] == 'waiting_for_phone':
            user_data[user_id]['phone'] = message
            save_to_db(user_id, user_data[user_id])  # Сохраняем в БД
            del user_state[user_id]
            send_message(user_id, "Регистрация завершена!", get_keyboard("main"))

    return 'ok'

# Оригинальная функция send_message
def send_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.getrandbits(64),
        keyboard=keyboard.get_keyboard() if keyboard else None
    )

if __name__ == '__main__':
    app.run()
