from abc import ABCMeta, abstractmethod


class BotCommand(metaclass=ABCMeta):

    @abstractmethod
    def execute(self, message):
        pass


class ChangeBotResourceCommand(BotCommand):

    __keyboard = None
    user_input = False
    id = '/resource'

    def __init__(self, bot):
        self.bot = bot
        self.keyboard = [(r,v.resource_name) for r,v in bot.resources.items()]

    def execute(self, message):
        print('Executing command {}'.format(self.id))
        if not self.bot.is_callback(message):
            # Отправить пользователю клавиатуру, чтобы получить от него колбэк-параметр
            self.bot.send_message('Текущий ресурс: {}. Выберите ресурс'.format(self.bot.active_resource.resource_name),
                         message.chat['id'],
                         keyboard=self.keyboard)
        else:
            # обработать информацию из колбэк-параметров
            self.bot.active_resource = message.data
            self.bot.send_message('Ресурс успешно изменен! Текущий русурс: {}'.format(self.bot.active_resource.resource_name),
                           message.message['chat']['id'])
            self.bot.active_command = False

    @property
    def keyboard(self):
        return self.__keyboard

    @keyboard.setter
    def keyboard(self, keys_data):
        self.__keyboard = [[{'text': key[0], 'callback_data': key[1]}] for key in keys_data]


class ChangeBotResourceOptionsCommand(BotCommand):

    id = '/options'
    user_input = False
    active_option = None
    __keyboard = None

    def __init__(self, bot):
        self.bot = bot
        if getattr(bot.active_resource, 'get_options'):
            self.keyboard = [(id, option) for id, option in bot.active_resource.get_options().items()]

    @property
    def keyboard(self):
        return self.__keyboard

    @keyboard.setter
    def keyboard(self, keys_data):
        self.__keyboard = [[{'text': key[1].name, 'callback_data': key[0]}] for key in keys_data]

    def execute(self, message):
        if len(self.bot.active_resource.get_options()):
            if not self.bot.is_callback(message):
                if not self.user_input:
                    # Отправить пользователю клавиатуру, чтобы получить от него колбэк-параметр
                    self.bot.send_message('Выберите опцию: ', message.chat['id'],keyboard=self.keyboard)
                else:
                    try:
                        self.active_option.value(message.text)
                    except AssertionError as e:
                        return self.bot.send_message(str(e), message.chat['id'])
                    self.bot.send_message('Опция успешно изменена!', message.chat['id'])
                    self.bot.active_command = False
            else:
                # обработать информацию из колбэк-параметров
                self.active_option = self.bot.active_resource.get_options()[message.data]
                self.bot.send_message(self.active_option.message, message.message['chat']['id'])
                self.user_input = True
        else:
            self.bot.active_command = False
            self.bot.send_message('Для этого ресурса нет доступных опций', message.chat['id'])


class GetHelpCommand(BotCommand):

    id = '/help'

    def __init__(self, bot):
        self.bot = bot

    def execute(self, message):
        self.bot.send_message('Опция временно недоступна!', message.chat['id'])
        self.bot.active_command = False