import requests
import time
import json
from collections import namedtuple
from gamekeeper.resources.plati_ru import Plati
from gamekeeper.resources.yuplay import YuPlay


# Словарь ресурсов
__resources = {'plati.ru': Plati, 'yuplay.ru': YuPlay}

__user_input = False

# Структура данных команды для бота
Command = namedtuple('Command', ['name', 'command', 'message', 'keyboard'])

def get_resource(resource_name=None):
    """
    Получает объект ресурса по его названию
    :param resource_name:
    :return:
    """
    return __resources.get(resource_name, __resources['plati.ru'])

# TODO:: Сделать декоратор для ввода произвольного значения пользователем
def change_resource_options_command(option):
    print(option)
    r = resource.get_options()['option']
    return "Укажите значение опции: ..."

def get_command(command_name):
    """
    Получает объект исполняемой команды из словаря команд по ее названию
    :param command_name:
    :return:
    """
    return __commands.get(command_name)

def change_resource_command(resource_name):
    """
    Переопределяет текущий ресурс
    :param resource_name: название ресурса
    :return:
    """
    global resource
    resource = get_resource(resource_name)()
    return 'Ресурс успешно изменен! Текущий русурс: {}'.format(resource.resource_name)

def get_keyboard(command_name):
    """
    Словарь инлайн-клавиатур соответсвующих каждой комманде
    :param command_name:
    :return:
    """
    keyboards = {
        'resource' :
            [
                [{
                    'text': name,                # отображаемое название кнопки на инлайн-клавиатуре
                    'callback_data': json.dumps( # строка данных, которые передаются в теле ответа после нажатия кнопки
                        {'command_name': command_name, 'command_value': name})
                }] for name in __resources ],    # Клавиатура состоит из списка списков кнопок
        'help': None,
        'options': [[{'text': option, 'callback_data': json.dumps({
            'command_name': command_name, 'command_value': option
        })}] for option in resource.get_options()]
    }
    return keyboards.get(command_name)

def get_help_command():
    return 'Помощь уже в пути!'

def info():
    return requests.get(__telegram_api.get('INFO').format(__token)).json()

def __update(offset=None, timeout=100):
    return requests.get(__telegram_api.get('UPDATES').format(__token), params={
        'offset': offset,
        'timeout': timeout
    }).json()

def __send(message_type):
    def sender_type(message):
        def sender(*args, **kwargs):
            return requests.post(__telegram_api.get(message_type).format(__token), data=message(*args, **kwargs))
        return sender
    return sender_type

def __send_with_keyboard(message):
    def message_with_keyboard(*args, **kwargs):
        msg = message(*args, **kwargs)
        if kwargs.get('keyboard'):
            msg['reply_markup'] = json.dumps({"inline_keyboard": kwargs['keyboard']})
        return msg
    return message_with_keyboard

@__send('MESSAGE')
@__send_with_keyboard
def send_message(message, chat_id, parse_mode=None, reply_id=None, disable_web_page_preview=True, keyboard=None):
    return {
        'chat_id':chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'reply_to_message_id': reply_id,
        'disable_web_page_preview': disable_web_page_preview,
    }

@__send('CALLBACK')
def answer_callback(answer):
    return {
        'callback_query_id' : answer['id'],
        'text': answer['message']
    }

def execute_callback(callback):
    data = json.loads(callback.data)
    message = __commands.get('/' + data['command_name']).command(data['command_value'])
    return {'message': message, 'id': callback.id}

def __get_message(msg: dict) -> namedtuple:
    """
    Принимает объект сообщения и парсит его на составляющие
    Возращает именованный картеж
    :param msg:
    :return:
    """
    message_fields = ('chat','text','from_user','entities','message_id','date','sticker','photo','document',
                      'reply_to_message', 'id', 'chat_instance', 'message', 'data')
    Message = namedtuple('Message', message_fields)
    for field in message_fields:
        if field not in msg: msg[field] = None
    try:
        msg['from_user'] = msg['from']                  # Нельзя использовать 'from' в качестве названия поля
        del msg['from']
        message = Message(**msg)
    except TypeError:
        error_msg = {'chat': msg['chat'], 'text': 'Извините, я не понял Ваше сообщение', 'from': None}
        message = __get_message(error_msg)
    return message

def __define_update_type(update):
    update_types = ['message', 'edited_message', 'callback_query']
    type = next(filter(update.get, update_types))       # определяет тип обновления
    return __get_message(update[type])

def is_command(msg):
    if msg.entities:
        return next(filter(lambda entity: entity.get('type') == 'bot_command', msg.entities))

def chunk_string(string):
    split_mark = string.index('\t', 5000)
    return string[:split_mark], string[split_mark:]

def run(handler=None):
    print('Listening...')
    last_update_id= None
    while True:
        try:
            updates = __update(offset=last_update_id)['result'][0]
            last_update_id = updates['update_id'] + 1
            message = __define_update_type(updates)
            handler(message) if handler else print(updates)
        except IndexError:
            continue
        time.sleep(0.5)


# ПЕРЕМЕННЫЕ
# ===================================================================

__token = open('../.env').readline().split('=')[1].strip()

# Основные интерфейсы Телеграма
__telegram_api = {
    'INFO': 'https://api.telegram.org/bot{}/getme',
    'UPDATES': 'https://api.telegram.org/bot{}/getUpdates',
    'MESSAGE': 'https://api.telegram.org/bot{}/sendMessage',
    'CALLBACK': 'https://api.telegram.org/bot{}/answerCallbackQuery'
}

# Текущий ресурс для поиска игры
resource = get_resource()()

# Словарь команд
__commands = {
    '/resource': Command(name='resource', command=change_resource_command,
                         message='Текущий ресурс: {}. Выберите ресурс'.format(resource.resource_name),
                         keyboard=get_keyboard),
    '/help': Command(name='help', command=get_help_command,
                     message='Помощь уже в пути',
                     keyboard=get_keyboard),
    '/options': Command(name='options', command=change_resource_options_command,
                        message='Опции', keyboard=get_keyboard)
}
