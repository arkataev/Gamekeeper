import time
from gamekeeper.bot.bot import Bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import (ChangeBotResourceCommand,
                                     ChangeBotResourceOptionsCommand,
                                     GetHelpCommand,
                                     BotStartCommand)


bot_commands = [ChangeBotResourceCommand,
                ChangeBotResourceOptionsCommand,
                GetHelpCommand,
                BotStartCommand]
bot_resources = [Plati, YuPlay]

def default_handler(msg):
    try:
        if not msg.from_user:
            Bot.send_message(msg.text, msg.chat['id'])
        else:
            user_id = msg.from_user['id']
            bot = Bot.create(user_id, resources=bot_resources, commands=bot_commands)
            if Bot.is_command(msg) or Bot.is_callback(msg) or bot.active_command: return bot.execute(msg)
            start_time = time.time()
            Bot.send_message('<i>Сейчас посмотрим...</i>', msg.chat['id'], parse_mode='HTML')
            result = str(bot.active_resource.search(msg.text))
            if len(result) > 5000:
                for chunk in Bot.chunk_string(result):
                    Bot.send_message(chunk, msg.chat['id'], parse_mode='HTML')
            else:
                Bot.send_message(result, msg.chat['id'], parse_mode='HTML')
            print("--- Result length: {} Searched for: {:.2} seconds ---".format(len(result),
                                                                                 float(time.time() - start_time)))
    except BaseException as e:
        print(e)
        return Bot.send_message('Ой! Что-то пошло не так', msg.chat['id'])

Bot.run(default_handler)
