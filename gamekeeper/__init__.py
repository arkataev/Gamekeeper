from gamekeeper.bot import bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay


def bot_msg_handler(msg):
    # Пользователь с помощью команды боту выбирает ресурс для поиска (ресурс выбирать на интерактивной клавиатуре)
    # Бот получает в сообщении от пользователя строку для поиска
    # Отправляет запрос в метод search выбранного ресурса
    # Получает результат поиска и отправляет в ответе пользователю

    # Получить из сообщения команду
    # Если команда - resource, вернуть клавиатуру с выбором варианта ресурсов

    resource = Plati()
    if getattr(resource, 'rating', False):
        resource.rating = 200
    result = resource.search(msg.text)
    bot.send(str(result), msg.chat['id'], parse_mode='HTML')

bot.run(bot_msg_handler)
