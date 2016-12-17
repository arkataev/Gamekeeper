from gamekeeper.bot import bot



def bot_msg_handler(msg):
    bot.send(msg.text, msg.chat['id'])

bot.run(bot_msg_handler)
