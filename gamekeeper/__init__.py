from gamekeeper.bot import bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
import time

def default_handler(msg):
    if bot.is_command(msg):
        command = bot.get_command(msg.text)
        return bot.send_message(command.message, msg.chat['id'], keyboard=command.keyboard(command.name))
    if msg.chat_instance:
        callback_result = bot.execute_callback(msg)
        return bot.answer_callback(callback_result)

    if getattr(bot.resource, 'rating', False):
        bot.resource.rating = 200
    start_time = time.time()
    result = str(bot.resource.search(msg.text))
    if len(result) > 5000:
        for chunk in bot.chunk_string(result):
            bot.send_message(chunk, msg.chat['id'], parse_mode='HTML')
    else:
        bot.send_message(result, msg.chat['id'], parse_mode='HTML')

    print(len(result))
    print("--- {} seconds ---".format(time.time() - start_time))

bot.run(default_handler)
