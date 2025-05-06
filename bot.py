import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

null_keyboard = VkKeyboard()
null_keyboard.add_button('На главную', color = VkKeyboardColor.PRIMARY)

main_keyboard = VkKeyboard()
main_keyboard.add_button('Расписание')
main_keyboard.add_line()
main_keyboard.add_button('Частые вопросы')
main_keyboard.add_line()
main_keyboard.add_button('Свой вопрос')
main_keyboard.add_line()
main_keyboard.add_button('Напоминания')

schedule_keyboard = VkKeyboard()
schedule_keyboard.add_button('Неделя')
schedule_keyboard.add_line()
schedule_keyboard.add_button('Кружок')
schedule_keyboard.add_line()
schedule_keyboard.add_button('Мероприятия')
schedule_keyboard.add_line()
schedule_keyboard.add_button('На главную', color = VkKeyboardColor.PRIMARY)

class_keyboard = VkKeyboard()
class_keyboard.add_button('Время')
class_keyboard.add_line()
class_keyboard.add_button('Запомнить')
class_keyboard.add_line()
class_keyboard.add_button('Назад', color = VkKeyboardColor.PRIMARY)
class_keyboard.add_button('На главную', color = VkKeyboardColor.PRIMARY)

questions_keyboard = VkKeyboard()
questions_keyboard.add_button('Категория')
questions_keyboard.add_line()
questions_keyboard.add_button('Свой вопрос')
questions_keyboard.add_line()
questions_keyboard.add_button('На главную', color = VkKeyboardColor.PRIMARY)

topic_keyboard = VkKeyboard()
topic_keyboard.add_button('Вопрос')
topic_keyboard.add_line()
topic_keyboard.add_button('Назад', color = VkKeyboardColor.PRIMARY)
topic_keyboard.add_button('На главную', color = VkKeyboardColor.PRIMARY)

def write_message(sender, message, keyboard):
  authorize.method('messages.send', {'user_id': sender, 'message': message, 'random_id': get_random_id(), 'keyboard': keyboard.get_keyboard()})

token = "vk1.a.92y-_Kt4NuqPY45s73_0FecEPVsFgOu3dmKnzRDRVh0WJt7sya8tiSVqZfl_SMOzv-C8gZTAbiJzjjdhsImI2K0RB7gXbWKxLROpHiyQq9rgR9Ko4CobGsycjajLINleTOYYtvWazH6GU099Tl7x-IbuMsqVJYhbV3zw5VDLt9TqBFhljAvyHGycNxZYFzJNtikhnxGkEk8Ei-W4au2tlQ"
authorize = vk_api.VkApi(token = token)
longpoll = VkLongPoll(authorize)

for event in longpoll.listen():
  if event.type == VkEventType.MESSAGE_NEW and event.text:
    reseived_message = event.text
    sender = event.user_id
    flag = 0

    if reseived_message == "Начать":
      write_message(sender, "Приветствуем тебя в молодежном клубе «Острова». Мы – часть большой семьи молодежного центра «Охта» Красногвардейского района. Мы с радостью ответим на ваши вопросы.\nМы предоставляем место для спортивных и креативных личностей, стремящихся улучшить свои навыки или просто хорошо провести время в компании единомышленников.", null_keyboard)

    elif reseived_message == "На главную":
      write_message(sender, "Вот небольшое меню для более общей информации. Вы можете посмотреть наше расписание на ближайшую неделю и записаться на мероприятие, посмотреть на часто задаваемые вопросы или, если не смогли найти нужною информацию, обратиться к сотруднику.", main_keyboard)

    elif reseived_message == "Расписание" or reseived_message == "Назад" and flag == 1:
      flag = 1
      write_message(sender, "Вот информация про события на эту неделю.", schedule_keyboard)
      
    elif reseived_message == "Кружок":
      write_message(sender, "(Информация про кружок)", class_keyboard)
      
    elif reseived_message == "Частые вопросы" or reseived_message == "Назад" and flag == 2:
      flag = 2
      write_message(sender, "Что вы хотите узнать? ", questions_keyboard)

    elif reseived_message == "Категория":
      write_message(sender, "Список вопросов этой категории:", topic_keyboard)
      
    elif reseived_message == "Вопрос":
      write_message(sender, "(Ответ)", topic_keyboard)
      
    elif reseived_message == "Свой вопрос":
      write_message(sender, "Оператор ответит вам в течении Х времени, ожидайте.", null_keyboard)
      
