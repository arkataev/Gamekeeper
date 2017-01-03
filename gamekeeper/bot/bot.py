import requests
import time
import json
from collections import namedtuple
from gamekeeper.resources.resource import absResource



class Bot:

    # Доступные ресурсы для поиска игры
    __resources = {}
    # Доступные команды бота
    __commands = None
    # Активная комманда бота
    __active_command = None
    # Активный ресурс для поиск игры
    __active_resource = None
    # токен Бота
    __token = open('../.env').readline().split('=')[1].strip()
    # Основные интерфейсы Телеграма
    __telegram_api = {
        'INFO': 'https://api.telegram.org/bot{}/getme',
        'UPDATES': 'https://api.telegram.org/bot{}/getUpdates',
        'MESSAGE': 'https://api.telegram.org/bot{}/sendMessage',
        'CALLBACK': 'https://api.telegram.org/bot{}/answerCallbackQuery'
    }

    def __init__(self, resources, commands=None):
        self.resources = resources
        self.commands = commands
        self.active_resource = resources[0].resource_name # По умолчанию использовать первый ресурс в списке

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
        self.__commands = {command.id:command for command in commands_list}

    @resources.setter
    def resources(self, resources_list):
        if resources_list:
            for resource in resources_list:
                assert issubclass(resource, absResource), 'Resource is not an absResource subclass'
                self.resources[resource.resource_name.lower()] = resource

    @active_resource.setter
    def active_resource(self, resource_name):
        self.__active_resource = self.get_resource(str(resource_name).lower())()

    @active_command.setter
    def active_command(self, command):
        # assert command is Command, 'Command is not an absCommand subclass'
        self.__active_command = command

    def __update(self, offset=None, timeout=100):
        return requests.get(self.__telegram_api.get('UPDATES').format(self.__token), params={
            'offset': offset,
            'timeout': timeout
        }).json()

    def __send(self, message_type):
        def sender(message):
            return requests.post(self.__telegram_api.get(message_type).format(self.__token),
                                 data=message)
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









# # Словарь ресурсов
# __resources = {'plati.ru': Plati, 'yuplay.ru': YuPlay}
# # Ресурс для поиска игры (по умолчанию - Плати.ру)
# resource = Plati()
# # Активная команда для бота
# active_command = None
# # Структура данных команды для бота
# Command = namedtuple('Command', ['name', 'command', 'keyboard', 'user_input'])
#
#
#
# def change_resource_option_command(option):
#     print(option)
#     resource_option = resource.get_options()[option]
#     print(resource_option)
#     return "Укажите значение опции: ..."
#

#
# def change_resource_command(msg):
#     global resource
#     global active_command
#     if not is_callback(msg):
#         # Отправить пользователю клавиатуру, чтобы получить от него колбэк-параметр
#         send_message('Текущий ресурс: {}. Выберите ресурс'.format(resource.resource_name),
#                      msg.chat['id'],
#                      keyboard=active_command.keyboard(active_command.name))
#     else:
#         # обработать информацию из колбэк-параметров
#         data = json.loads(msg.data)
#         resource_name = data['command_value']
#         resource = get_resource(resource_name)
#         send_message('Ресурс успешно изменен! Текущий русурс: {}'.format(resource.resource_name),
#                        msg.message['chat']['id'])
#         active_command = False
#
# def get_keyboard(command_name):
#     """
#     Словарь инлайн-клавиатур соответсвующих каждой комманде
#     :param command_name:
#     :return:
#     """
#     keyboards = {
#         'resource' :
#             [
#                 [{
#                     'text': name,                # отображаемое название кнопки на инлайн-клавиатуре
#                     'callback_data': json.dumps( # строка данных, которые передаются в теле ответа после нажатия кнопки
#                         {'command_name': command_name, 'command_value': name})
#                 }] for name in __resources ],    # Клавиатура состоит из списка списков кнопок
#         'options': [[{'text': option, 'callback_data': json.dumps({
#             'command_name': command_name, 'command_value': option
#         })}] for option in resource.get_options()]
#     }
#     return keyboards.get(command_name)
#
# def get_help_command(params=None):
#     return 'Помогаю всем!'
#
# def info():
#     return requests.get(__telegram_api.get('INFO').format(__token)).json()
#
#
#
#
#
#
#
#
#
# def execute(msg):
#     global active_command
#     if is_command(msg): active_command = get_command(msg.text)
#     try:
#         active_command.command(msg)
#     except AttributeError as e:
#         print(e)
#     #     if active_command.keyboard:
#     #         # Отправить пользователю клавиатуру для получения параметров выполнения команды
#     #         send_message(active_command.message, msg.chat['id'], keyboard=active_command.keyboard(active_command.name))
#     #     else:
#     #         # Отправить пользователю результат выполнения команды
#     #         send_message(active_command.command(msg), msg.chat['id'])
#     #         # Если ввод данных от пользователя не требутся отключить активную команду
#     #         if not active_command.user_input: active_command = False
#     # elif is_callback(msg):
#     #     data = json.loads(msg.data)
#     #     # Выполнить команду с использованием данных из инлайн-запроса
#     #     message = active_command.command(data['command_value'])
#     #     # Ответить пользователю уведомлением
#     #     send_callback({'message': message, 'id': msg.id})
#     # else:
#     #     # Выполнить команду с ипользованием данных введенных пользователем и ответить пользователю сообщением
#     #     send_message(active_command.command(msg), msg.chat['id'])
#     #     # Выключить активную команду
#     #     active_command = False
#     # return True
#
#
#
#
#
#
#
#
# # ПЕРЕМЕННЫЕ
# # ===================================================================
#
#
#
#
#
# # Словарь команд
# __commands = {
#     '/resource': Command(name='resource', command=change_resource_command,keyboard=get_keyboard, user_input=False),
#     '/help': Command(name='help', command=get_help_command, keyboard=get_keyboard, user_input=False),
#     '/options': Command(name='options', command=change_resource_option_command, keyboard=get_keyboard, user_input=True)
# }
