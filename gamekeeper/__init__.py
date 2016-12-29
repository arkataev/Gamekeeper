from gamekeeper.bot import bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from itertools import islice

def bot_msg_handler(msg):
    # Пользователь с помощью команды боту выбирает ресурс для поиска (ресурс выбирать на интерактивной клавиатуре)
    # Бот получает в сообщении от пользователя строку для поиска
    # Отправляет запрос в метод search выбранного ресурса
    # Получает результат поиска и отправляет в ответе пользователю

    resource = YuPlay()
    result = resource.search(msg.text)
    # response = "\n".join([seller for seller in islice(result, 10)])
    bot.send(str(result), msg.chat['id'], parse_mode='HTML')

bot.run(bot_msg_handler)
