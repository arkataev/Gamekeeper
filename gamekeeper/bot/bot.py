import requests
import time
import json
from collections import namedtuple, OrderedDict
from gamekeeper.bot.commands import BotCommand
from gamekeeper.bot.exceptions import BotException, BotCommandException


# Модель сообщения, с которой работает бот
BotMessage = namedtuple('BotMessage', ('chat', 'text', 'from_user', 'entities', 'message_id', 'date',
                                         'sticker', 'photo', 'document', 'reply_to_message', 'id', 'chat_instance',
                                         'message', 'data', 'update_id', 'voice', 'contact', 'bot_command', 'callback'))

class TelegramBot:

    """
    Класс бота для Телеграмма.
    """

    # Активная комманда
    active_command = None
    # Доступные команды бота
    commands = None
    # Основные интерфейсы Телеграма
    _telegram_api = {
        'INFO': 'https://api.telegram.org/bot{}/getme',
        'UPDATES': 'https://api.telegram.org/bot{}/getUpdates',
        'MESSAGE': 'https://api.telegram.org/bot{}/sendMessage',
        'CALLBACK': 'https://api.telegram.org/bot{}/answerCallbackQuery'
    }
    # Коллекция созданных ботов
    _bot_que = OrderedDict()
    # Лимит экземпляров бота в коллекции
    bot_limit = None
    # токен бота для доступа к API
    token= None
    # Словарь фраз
    vocabulary = None

    def __init__(self, bot_id):
        """
        Бот принимает в качестве параметров список ресурсов и
        список команд
        """
        self.id = bot_id
        print('A new Bot was created! Id: {}'.format(self.id))

    def send_message(self, message:str, parse_mode:str='HTML', reply_id:int=None, disable_web_page_preview:bool=True,
                     keyboard:list=None):
        """
        Отправить сообщение пользователю
        :param message:
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
        fixed-width text or inline URLs in your bot's message.
        :param reply_id: If the message is a reply, ID of the original message
        :param disable_web_page_preview: Disables link previews for links in this message
        :param keyboard: Additional interface options. A JSON-serialized object for an inline keyboard,
         custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return:
        """
        message = {
            'chat_id': self.id,
            'text': message,
            'parse_mode': parse_mode,
            'reply_to_message_id': reply_id,
            'disable_web_page_preview': disable_web_page_preview,
        }
        sender = self.__send('MESSAGE')
        if keyboard: message['reply_markup'] = json.dumps({"inline_keyboard": keyboard})
        return sender(message)

    def send_callback(self, answer:dict):
        message =  {
            'callback_query_id': answer['id'],
            'text': answer['message']
        }
        sender = self.__send('CALLBACK')
        return sender(message)

    def execute(self, bot_message):
        """
        Выполнить команду
        :param bot_message:
        :return:
        """
        try:
            if bot_message.bot_command:
                command = self._get_command(bot_message.text)
                self.active_command = command(self)
            self.active_command.execute(bot_message)
        except BotException as e:
            print(e)
        except:
            raise BotCommandException(bot_message.text, "Ошибка выполнения команды")

    def speak(self, key):
        return self.vocabulary.get(key, None)

    def log_search(self, query, search_time, found, length):
        return ("{:*^30}\n"
          "Bot id: {.id}\n"
          "Query: {}\n"
          "Resource: {.active_resource.resource_name}\n"
          "Message length: {} \n"
          "Found: {} items \n"
          "Time: {:.2} sec.").format(" Search Completed! ", self, query, self, length, found, search_time)

    @classmethod
    def run(cls,handler=None):
        """
        Основной цикл работы бота.
        Бот получает обновления сообщений от сервера Телеграм,
        формирует из них сообщения и отправляет в обработчик сообщений переданный в качестве
        параметра
        :param handler: Функция - обработчик сообщений
        :return:
        """
        print('Listening...')
        last_update_id = None
        while True:
            try:
                updates = cls._update(offset=last_update_id,
                                     allowed_updates=['message', 'edited_message', 'callback_query'])['result'][0]
                last_update_id = updates['update_id'] + 1
                message = TelegramBot._get_message(updates)
                handler(message) if handler else print(updates)
            except IndexError:
                continue
            except BotCommandException as e:
                print("{}: {}".format(e, e.command))
            except BotException as e:
                print(e)
            time.sleep(0.5)

    @classmethod
    def _update(cls, offset: int = None, timeout=100, allowed_updates: list = None):
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
        updates = requests.get(cls._telegram_api.get('UPDATES').format(cls.token), params={
            'offset': offset,
            'timeout': timeout,
            'allowed_updates': allowed_updates
        })
        if not updates: raise BotException('Не удалось получить обновления от сервера Телеграмм')
        return updates.json()


    @classmethod
    def create(cls, bot_id:int, *args, **kwargs) -> object:
        """
        Фабрика Ботов
        :param bot_id: Идентификатор пользователя, приславшего сообщение
        :type bot_id: int
        :return: new Telegram Bot instance
        """
        bot = cls._bot_que.get(bot_id, None)
        if not bot:
            bot = cls(bot_id, *args, **kwargs)
            if len(cls._bot_que) > int(cls.bot_limit): cls._bot_que.popitem(last=False)
            cls._bot_que[bot_id] = bot
        return bot

    @classmethod
    def set_commands(cls, commands_list):
        cls.commands = {command.id: command for command in commands_list if issubclass(command, BotCommand)}

    @staticmethod
    def chunk_string(string):
        split_mark = string.index('\t', 5000)
        return string[:split_mark], string[split_mark:]

    @staticmethod
    def _get_message(update: dict) -> BotMessage or False:
        """
        Создает модель сообщения для использования ботом
        https://core.telegram.org/bots/api#update
        :param update:
        :type update: dict
        :return: namedtuple or bool
        """
        bot_message = dict.fromkeys(BotMessage._fields)
        # update_id - обязательный элемент в обновлении
        update_id = update.pop('update_id')
        # кроме update_id в обновлении может находиться не более одного дополнительного элемента
        update_kind, update_body = update.popitem()
        bot_message.update(update_body)
        # Нельзя использовать 'from' в качестве названия поля namedtuple поэтому заменяем
        bot_message['from_user'] = bot_message.pop('from')
        # Добавляем тип сообщения и идентификатор обновления
        # bot_message['kind'] = update_kind
        bot_message['update_id'] = update_id
        # Определяем есть ли в обновлении специальные элементы
        entities = bot_message.get('entities')
        if entities:
            for ent in entities: bot_message[ent['type']] = True
        if update_kind == 'callback_query': bot_message['callback'] = True
        # Создаем сообщение для бота
        try:
            return BotMessage(**bot_message)
        except TypeError:
            raise BotException('Не удалось создать модель сообщения')

    def __send(self, message_type):
        def sender(message):
            sent_message = requests.post(self._telegram_api.get(message_type).format(self.token), data=message)
            if not sent_message: raise BotException('Не удалось отправить сообщение пользователю')
        return sender

    def _get_command(self, command_name:str) -> object or None:
        """
        Получает объект исполняемой команды из словаря команд по ее названию
        :param command_name:
        :return:
        """
        command = self.commands.get(command_name)
        if not command: raise BotException("Комманда не найдена")
        return command


class Gamekeeper(TelegramBot):

    # Доступные ресурсы для поиска игры
    resources = {}
    # Активный ресурс
    __active_resource = None

    @property
    def active_resource(self):
        return self.__active_resource

    @active_resource.setter
    def active_resource(self, resource_name):
        self.__active_resource = self.__get_resource(str(resource_name).lower())()

    def search(self, query):
        # Время начала поиска
        start_time = time.time()
        # Сообщаем пользователю о начале поиска
        self.send_message('<i>{}</i>'.format(self.speak('search')))
        # Результат поиска
        result = self.active_resource.search(query)
        # Длительность поиска в секундах
        search_time = time.time() - start_time
        # Количество найденных результатов
        count_results = 0 if not result else result.count_results()
        # Сообщение о результате поиска, которое будет отправлено пользователю
        message = self.speak('found_none') if not result else str(result)
        # Выводим лог поиска в консоль
        print(self.log_search(query, search_time, count_results, len(message)))
        return message

    @classmethod
    def set_resources(cls, resources_list):
        # По умолчанию бот будет использовать первый ресурс в списке для поиска игры
        cls.__active_resource = resources_list[0]()
        for resource in resources_list:
            cls.resources[resource.resource_name.lower()] = resource

    def __get_resource(self,resource_name:str) -> object or None:
        """
        Получает объект ресурса по его названию
        :param resource_name:
        :return:
        """
        resource =  self.resources.get(resource_name)
        if not resource: raise BotException("Ресурс не найден")
        return resource