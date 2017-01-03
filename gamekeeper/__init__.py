import time
import os
from gamekeeper.bot.bot import Bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import (ChangeBotResourceCommand,
                                     ChangeBotResourceOptionsCommand,
                                     GetHelpCommand)

# Токен для бота в телеграмм
token = open(os.getcwd() + '/gamekeeper/.env').readline().split('=')[1].strip()

# Экземпляр бота
bot = Bot(token, resources=[Plati, YuPlay], commands=[
    ChangeBotResourceCommand,
    ChangeBotResourceOptionsCommand,
    GetHelpCommand
])

def default_handler(msg):
    if bot.is_command(msg) or bot.active_command:
        try:
            return bot.execute(msg)
        except BaseException as e:
            print(e)
            return bot.send_message('Ой! Что-то пошло не так', msg.chat['id'])
    start_time = time.time()
    bot.send_message('<i>Сейчас посмотрим...</i>', msg.chat['id'], parse_mode='HTML')
    result = str(bot.active_resource.search(msg.text))
    if len(result) > 5000:
        for chunk in Bot.chunk_string(result):
            bot.send_message(chunk, msg.chat['id'], parse_mode='HTML')
    else:
        bot.send_message(result, msg.chat['id'], parse_mode='HTML')
    print("--- Searched for: {} seconds ---".format(time.time() - start_time))

bot.run(default_handler)
