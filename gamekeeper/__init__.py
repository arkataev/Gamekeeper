from gamekeeper.bot.bot import Bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
from gamekeeper.bot.commands import ChangeBotResourceCommand
import time


bot = Bot(resources=[Plati, YuPlay], commands=[ChangeBotResourceCommand])


def default_handler(msg):
    if bot.is_command(msg) or bot.active_command:
        return bot.execute(msg)
    start_time = time.time()
    result = str(bot.active_resource.search(msg.text))
    if len(result) > 5000:
        for chunk in Bot.chunk_string(result):
            bot.send_message(chunk, msg.chat['id'], parse_mode='HTML')
    else:
        bot.send_message(result, msg.chat['id'], parse_mode='HTML')
    print("--- {} seconds ---".format(time.time() - start_time))

bot.run(default_handler)
