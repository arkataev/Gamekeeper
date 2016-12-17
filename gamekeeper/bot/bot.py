import requests
import time
from collections import namedtuple


__token = '324178536:AAHMpH0ldMKHwlRvnffjifcoPNVPrNhmYvc'
__telegram_api = {
    'INFO': 'https://api.telegram.org/bot{}/getme',
    'UPDATES': 'https://api.telegram.org/bot{}/getUpdates',
    'SEND':'https://api.telegram.org/bot{}/sendMessage'
}

def info():
    return requests.get(__telegram_api.get('INFO').format(__token)).json()

def __update(offset=None, timeout=100):
    return requests.get(__telegram_api.get('UPDATES').format(__token), params={
        'offset': offset,
        'timeout': timeout
    }).json()

def send(message, chat_id, parse_mode=None, reply_id=None, disable_web_page_preview=True):
    return requests.post(__telegram_api.get('SEND').format(__token), data={
        'chat_id':chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'reply_to_message_id': reply_id,
        'disable_web_page_preview': disable_web_page_preview
    })

def __get_message(msg: dict) -> object:
    message_fields = ('chat','text','from_user','entities','message_id','date','sticker','photo','document',
                      'reply_to_message')
    Message = namedtuple('Message', message_fields)
    for field in message_fields:
        if field not in msg: msg[field] = None
    try:
        msg['from_user'] = msg['from']              # Нельзя использовать 'from' в качестве названия поля
        del msg['from']
        message = Message(**msg)
    except TypeError:
        # TODO:: Log Error
        error_msg = {'chat': msg['chat'], 'text': 'Извините, я не понял Ваше сообщение', 'from': None}
        message = __get_message(error_msg)
    return message

def command():
    pass


def run(handler=None):
    print('Listening...')
    print(info())
    last_update_id= None
    while True:
        updates = __update(offset=last_update_id)['result']
        if updates:
            last_update_id = updates[0]['update_id'] + 1
            message = __get_message(updates[0]['message'])
            handler(message) if handler else print(updates)
        time.sleep(0.5)
