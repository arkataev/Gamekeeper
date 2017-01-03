from gamekeeper.bot import bot
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay
import time

def default_handler(msg):
    print(bot.resource.resource_name)
    # Обработка команды для бота
    if bot.is_command(msg) or bot.is_callback(msg) or bot.active_command:
        # command = bot.get_command(msg.text)
        return bot.execute(msg)
        # return bot.send_message(command.message, msg.chat['id'], keyboard=command.keyboard(command.name))
    # Обработка инлайн-запроса
    # if msg.chat_instance:
    #     callback_result = bot.execute_callback(msg)
    #     return bot.answer_callback(callback_result)
    # Обработка сообщения
    # Проверить относится ли сообщение к выполнению команды (является параметром, например)
    # if bot.active_command:
    #     command = bot.active_command
    #     need_input = command.user_input
    #     if need_input:
    #         result = command.command(msg.text)

    # if getattr(bot.resource, 'rating', False):
    #     bot.resource.rating = 200
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
