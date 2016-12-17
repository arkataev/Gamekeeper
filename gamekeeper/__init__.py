from gamekeeper.bot import bot



def bot_msg_handler(msg):
    bot.send(msg.text, msg.chat['id'])

if __name__ == '__main__':
    bot.run(bot_msg_handler)

    # {'message': {
    #     'from': {'id': 54159458, 'first_name': 'Александр', 'username': 'arkataev'},
    #     'message_id': 110,
    #     'entities': [{'length': 6, 'type': 'bot_command', 'offset': 0}],
    #     'chat': {'id': 54159458, 'first_name': 'Александр', 'type': 'private', 'username': 'arkataev'},
    #     'text': '/greet',
    #     'date': 1481975069
    # },
    #     'update_id': 827649449
    # }
