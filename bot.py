import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import ret_random_id

def write_message(sender, message):
  authorize.method('messages.send', {'user_id': sender, 'message': message, 'random_id': get_random_id()})

token = "vk1.a.92y-_Kt4NuqPY45s73_0FecEPVsFgOu3dmKnzRDRVh0WJt7sya8tiSVqZfl_SMOzv-C8gZTAbiJzjjdhsImI2K0RB7gXbWKxLROpHiyQq9rgR9Ko4CobGsycjajLINleTOYYtvWazH6GU099Tl7x-IbuMsqVJYhbV3zw5VDLt9TqBFhljAvyHGycNxZYFzJNtikhnxGkEk8Ei-W4au2tlQ"
authorize = vk_api.VkApi(token = toker)
longpoll = VkLongPoll(authorize)
for ivent in longpool.listen():
  if event.type == VkEventType.MESSAGE_NEW and event.text:
    reseived_message = event.text
    sender = event.user_id
    if reseived_message == "Привет":
      write_message(sender, "Добрейшего")
