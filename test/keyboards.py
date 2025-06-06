from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def empty_kb():
    return VkKeyboard(one_time=False)

def get_keyboard(name):
    kb = VkKeyboard(one_time=False)
    if name == "main":
        kb.add_button('Личный кабинет')
        kb.add_line()
        kb.add_button('Кружки и Мероприятия')
        kb.add_line()
        kb.add_button('Вопросы')

    elif name == "personal_account":
        kb.add_button('Информация')
        kb.add_line()
        kb.add_button('Мои записи')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

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

    elif name == "edit_info":
        kb.add_button('Имя и Фамилия')
        kb.add_line()
        kb.add_button('Дата рождения')
        kb.add_line()
        kb.add_button('Номер телефона')
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "questions":
        kb.add_button('Часто задаваемые вопросы')
        kb.add_line()
        kb.add_button('Свой вопрос')
        kb.add_line()
        kb.add_button('На главную', color=VkKeyboardColor.PRIMARY)

    elif name == "confirm_registration":
        kb.add_button('Подтверждаю', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Не подтверждаю', color=VkKeyboardColor.NEGATIVE)

    elif name == "events_back":
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    elif name == "register_event":
        kb.add_button('Записаться!', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('Назад', color=VkKeyboardColor.PRIMARY)

    return kb
