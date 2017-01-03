import requests
import time
import json
from collections import namedtuple
from gamekeeper.bot.commands import BotCommand


class Bot:
    """
    Класс бота для Телеграмма. Бот по запросу пользователя ищет игры на
    доступных торговых площадках, а также может выполнять другие команды
    """

    # Доступные ресурсы для поиска игры
    __resources = {}
    # Доступные команды бота
    __commands = None
    # Активная команда, которая выполняется в данный момент
    __active_command = None
    # Активный ресурс, где будет производится поиск игры
    __active_resource = None
    # токен бота
    __token = open('../.env').readline().split('=')[1].strip()
    # Основные интерфейсы Телеграма
    __telegram_api = {
        'INFO': 'https://api.telegram.org/bot{}/getme',
        'UPDATES': 'https://api.telegram.org/bot{}/getUpdates',
        'MESSAGE': 'https://api.telegram.org/bot{}/sendMessage',
        'CALLBACK': 'https://api.telegram.org/bot{}/answerCallbackQuery'
    }

    def __init__(self, resources:list, commands:list=None):
        """
        Бот принимает в качестве параметров список ресурсов и
        список команд
        :param resources:
        :param commands:
        """
        self.resources = resources
        self.commands = commands
        # По умолчанию бот будет использовать первый ресурс в списке для поиска игры
        self.active_resource = resources[0].resource_name

    @property
    def active_resource(self):
        return self.__active_resource

    @property
    def resources(self):
        return self.__resources

    @property
    def commands(self):
        return self.__commands

    @property
    def active_command(self):
        return self.__active_command

    @commands.setter
    def commands(self, commands_list):
        self.__commands = {command.id:command for command in commands_list if issubclass(command, BotCommand)}

    @resources.setter
    def resources(self, resources_list):
        for resource in resources_list:
            self.resources[resource.resource_name.lower()] = resource

    @active_resource.setter
    def active_resource(self, resource_name):
        self.__active_resource = self.get_resource(str(resource_name).lower())()

    @active_command.setter
    def active_command(self, command):
        self.__active_command = command

    def __update(self, offset:int=None, timeout=100, allowed_updates:list=None):
        """
        Запрос к API-телеграмма для получения очереди сообщений

        :param offset: Identifier of the first update to be returned.
        Must be greater by one than the highest among the identifiers of previously received updates.
        By default, updates starting with the earliest unconfirmed update are returned.
        An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id.
        The negative offset can be specified to retrieve updates starting from -offset update from the end of the
        updates queue. All previous updates will forgotten.
        :param timeout: Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults to 100.
        :type offset: int
        :type allowed_updates: list
        :return:
        """
        return requests.get(self.__telegram_api.get('UPDATES').format(self.__token), params={
            'offset': offset,
            'timeout': timeout,
            'allowed_updates': allowed_updates
        }).json()

    def __send(self, message_type):
        def sender(message):
            return requests.post(self.__telegram_api.get(message_type).format(self.__token), data=message)
        return sender

    def send_message(self, message, chat_id, parse_mode=None, reply_id=None, disable_web_page_preview=True, keyboard=None):
        message = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'reply_to_message_id': reply_id,
            'disable_web_page_preview': disable_web_page_preview,
        }
        sender = self.__send('MESSAGE')
        if keyboard:
            message['reply_markup'] = json.dumps({"inline_keyboard": keyboard})
        return sender(message)

    def send_callback(self, answer):
        message =  {
            'callback_query_id': answer['id'],
            'text': answer['message']
        }
        sender = self.__send('CALLBACK')
        return sender(message)

    def get_command(self, command_name):
        """
        Получает объект исполняемой команды из словаря команд по ее названию
        :param command_name:
        :return:
        """
        return self.commands.get(command_name)

    def get_resource(self,resource_name):
        """
        Получает объект ресурса по его названию
        :param resource_name:
        :return:
        """
        return self.resources.get(resource_name)

    def execute(self, message):
        if Bot.is_command(message):
            command = self.get_command(message.text)
            self.active_command = command(self)
        try:
            self.active_command.execute(message)
        except BaseException as e:
            print(e)

    def run(self, handler=None):
        print('Listening...')
        last_update_id = None
        while True:
            try:
                updates = self.__update(offset=last_update_id)['result'][0]
                last_update_id = updates['update_id'] + 1
                message = Bot.__define_update_type(updates)
                handler(message) if handler else print(updates)
            except IndexError:
                continue
            time.sleep(0.5)

    @staticmethod
    def __define_update_type(update):
        update_types = ['message', 'edited_message', 'callback_query']
        type = next(filter(update.get, update_types))  # определяет тип обновления
        return Bot.__get_message(update[type])

    @staticmethod
    def is_command(msg):
        if msg.entities:
            return next(filter(lambda entity: entity.get('type') == 'bot_command', msg.entities))

    @staticmethod
    def chunk_string(string):
        split_mark = string.index('\t', 5000)
        return string[:split_mark], string[split_mark:]

    @staticmethod
    def is_callback(msg):
        return getattr(msg, 'chat_instance', False)

    @staticmethod
    def __get_message(msg: dict) -> namedtuple:
        """
        Принимает объект сообщения и парсит его на составляющие
        Возращает именованный картеж
        :param msg:
        :return:
        """
        message_fields = ('chat', 'text', 'from_user', 'entities', 'message_id', 'date', 'sticker', 'photo', 'document',
                          'reply_to_message', 'id', 'chat_instance', 'message', 'data')
        Message = namedtuple('Message', message_fields)
        for field in message_fields:
            if field not in msg: msg[field] = None
        try:
            msg['from_user'] = msg['from']  # Нельзя использовать 'from' в качестве названия поля
            del msg['from']
            message = Message(**msg)
        except TypeError:
            error_msg = {'chat': msg['chat'], 'text': 'Извините, я не понял Ваше сообщение', 'from': None}
            message = Bot.__get_message(error_msg)
        return message
