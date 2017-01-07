from gamekeeper.bot.bot import Gamekeeper, TelegramBot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import (ChangeBotResourceCommand, ChangeBotResourceOptionsCommand, GetHelpCommand,
                                     BotStartCommand)

Gamekeeper.set_commands([ChangeBotResourceCommand, ChangeBotResourceOptionsCommand, GetHelpCommand, BotStartCommand])
Gamekeeper.set_resources([Plati, YuPlay])
Gamekeeper.vocabulary = {
    'search': 'Сейчас посмотрим...',
    'found_none': 'К сожалению ничего найти не удалось :(',
    'greet': "Привет!"
}

def default_message_handler(bot_message):
    """
    Стандартный собработчик сообщений для бота
    :param bot_message:
    :type bot_message: namedtuple
    :return:
    """
    if not bot_message: return
    # Для каждого пользователя создается индивидуальный экземпляр бота
    # и помещается в очередь (Bot.bot_que)
    bot = Gamekeeper.create(bot_message.from_user['id'])
    # Обработка команд и связанных с ними сообщений
    if bot_message.bot_command or bot_message.callback or bot.active_command: return bot.execute(bot_message)
    # Обработка поисковых запросов
    result = bot.search(bot_message.text)
    if len(result) > 5000:
        # Телеграм не любит длинные сообщения поэтому лучше разбивать их на несколько меньших по размеру
        # Размер 5000 взят произвольно
        for chunk in Gamekeeper.chunk_string(result):
            bot.send_message(chunk)
    else: bot.send_message(result)
