from gamekeeper.bot.bot import Gamekeeper, BotMessage
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import (ChangeBotResourceCommand,
                                     ChangeBotResourceOptionsCommand,
                                     GetHelpCommand,
                                     BotStartCommand)

Gamekeeper.set_commands([ChangeBotResourceCommand, ChangeBotResourceOptionsCommand, GetHelpCommand, BotStartCommand])
Gamekeeper.set_resources([Plati, YuPlay])
Gamekeeper.set_vocabulary({
    'search': 'Сейчас посмотрим...',
    'found_none': 'К сожалению ничего найти не удалось :(',
    'greet': "Привет!"
})

def default_message_handler(msg:BotMessage):
    """
    Стандартный собработчик сообщений для бота
    :param msg:
    :type msg: __namedtuple
    :return:
    """
    if not msg: return
    # Для каждого пользователя создается индивидуальный экземпляр бота
    # и помещается в очередь (Bot.bot_que)
    bot = Gamekeeper.create(msg.from_user['id'])
    # Обработка команд и связанных с ними сообщений
    try:
        if msg.bot_command or bot.active_command: return bot.execute(msg)
        elif msg.kind == 'callback_query': return bot.resume_command(msg)
    except BaseException as e:
        print(e)
        return
    # Обработка поисковых запросов
    result = bot.search(msg.text)
    if len(result) > 5000:
        # Телеграм не любит длинные сообщения поэтому лучше разбивать их на несколько меньших по размеру
        # Размер 5000 взят произвольно
        for chunk in Gamekeeper.chunk_string(result):
            bot.send_message(chunk)
    else: bot.send_message(result)
