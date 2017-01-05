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
    # TODO:: Ошибка при получении пустого результата поиск 'str' object has no attribute 'count_results'
    print(msg)
    try:
        if not msg.from_user:
            Bot.send_message(msg.text, msg.chat['id'])
        else:
            user_id = msg.from_user['id']
            bot = Bot.create(user_id, resources=bot_resources, commands=bot_commands)
            if Bot.is_command(msg):
                return bot.execute(msg)
            elif bot.active_command:
                return bot.resume_command(msg)
            elif not Bot.is_callback(msg):
                start_time = time.time()
                Bot.send_message('<i>Сейчас посмотрим...</i>', bot.id, parse_mode='HTML')
                result = bot.active_resource.search(msg.text)
                if len(str(result)) > 5000:
                    for chunk in Bot.chunk_string(str(result)):
                        Bot.send_message(chunk, bot.id, parse_mode='HTML')
                else:
                    Bot.send_message(str(result), bot.id, parse_mode='HTML')
                print("{:*^30}\n"
                      "Bot id: {.id}\n"
                      "Query: {.text}\n"
                      "Resource: {.resource_name}\n"
                      "Message length: {} \n"
                      "Found: {} items \n"
                      "Time: {:.2} sec.".format(" Search result ", bot, msg, bot.active_resource,
                                                len(str(result)), result.count_results(),
                                                float(time.time() - start_time)))
    except BaseException as e:
        print(e)
        return Bot.send_message('Ой! Что-то пошло не так', bot.id)

Bot.run(default_handler)
