from abc import ABCMeta, abstractmethod

class BotCommand(metaclass=ABCMeta):

    _keyboard = None
    _user_input = False

    @property
    def user_input(self):
        return self._user_input

    @property
    def keyboard(self):
       return self._keyboard

    @abstractmethod
    def execute(self, message):
        pass

    def __init__(self, bot):
        self.bot = bot


class BotStartCommand(BotCommand):

    id = '/start'

    def execute(self, message):
        self.bot.send_message('Привет, {} !'.format(message.from_user['first_name']), message.chat['id'])
        self.bot.active_command = False


class ChangeBotResourceCommand(BotCommand):

    id = '/resource'

    def __init__(self, bot):
        super().__init__(bot)
        self.keyboard = [(r,v.resource_name) for r,v in bot.resources.items()]

    def execute(self, bot_message):
        if not bot_message.callback:
            # Отправить пользователю клавиатуру
            self.bot.send_message('Текущий ресурс: {}. Выберите ресурс'.format(
                self.bot.active_resource.resource_name), keyboard=self.keyboard)
        else:
            # обработать информацию из колбэк-параметров
            self.bot.active_resource = bot_message.data
            self.bot.send_message('Ресурс успешно изменен! Текущий русурс: {}'.format(
                self.bot.active_resource.resource_name))
            self.bot.active_command = False

    @BotCommand.keyboard.setter
    def keyboard(self, keys_data):
        self._keyboard = [[{'text': key[0], 'callback_data': key[1]}] for key in keys_data]


class ChangeBotResourceOptionsCommand(BotCommand):

    id = '/options'
    active_option = None

    def __init__(self, bot):
        super().__init__(bot)
        if getattr(bot.active_resource, 'get_options'):
            self.keyboard = [(id, option) for id, option in bot.active_resource.get_options().items()]

    @BotCommand.keyboard.setter
    def keyboard(self, keys_data):
        self._keyboard = [[{'text': key[1].name, 'callback_data': key[0]}] for key in keys_data]

    @BotCommand.user_input.setter
    def user_input(self, value):
        self._user_input = value

    def execute(self, bot_message):
        if not self.keyboard:
            self.bot.active_command = False
            return self.bot.send_message('Для этого ресурса нет доступных опций')
        if not bot_message.callback:
            if not self.user_input: return self.bot.send_message('Выберите опцию: ', keyboard=self.keyboard)
            try:
                self.active_option.value(bot_message.text)
            except AssertionError as e:
                return self.bot.send_message(str(e))
            self.bot.send_message('Опция успешно изменена!')
            self.bot.active_command = False
        else:
            # обработать информацию из колбэк-параметров
            self.active_option = self.bot.active_resource.get_options()[bot_message.data]
            self.bot.send_message(self.active_option.message)
            self.user_input = True


class GetHelpCommand(BotCommand):

    id = '/help'

    def execute(self, message):
        self.bot.send_message('Опция временно недоступна!')
        self.bot.active_command = False


class GetResourceNewsCommand(BotCommand):

    id = '/news'

    def execute(self, message):
        return



