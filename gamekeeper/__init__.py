import time
from gamekeeper.bot.bot import Bot, BotMessage, BotSpeak
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import (ChangeBotResourceCommand,
                                     ChangeBotResourceOptionsCommand,
                                     GetHelpCommand,
                                     BotStartCommand)

bot_commands = [ChangeBotResourceCommand, ChangeBotResourceOptionsCommand, GetHelpCommand, BotStartCommand]
bot_resources = [Plati, YuPlay]

def default_message_handler(msg:BotMessage):
    if not msg: return
    bot = Bot.create(msg.from_user['id'], resources=bot_resources, commands=bot_commands)
    if msg.bot_command or bot.active_command: return bot.execute(msg)
    elif msg.kind == 'callback_query': return bot.resume_command(msg)
    start_time = time.time()
    # TODO:: Отсылать сообщения от экземпляра бота, а не от класса
    Bot.send_message('<i>{}</i>'.format(BotSpeak['search']), bot.id, parse_mode='HTML')
    result = bot.active_resource.search(msg.text)
    count_results = result.count_results() if not isinstance(result,str) else 0
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
                                    len(str(result)), count_results,
                                    float(time.time() - start_time)))
