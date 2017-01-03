from collections import namedtuple

Key = namedtuple('Key', ['name', 'value'])
resources_keyboard = [Key(name='Plati.ru', value='plati.ru'), Key(name='Yuplay.ru', value='yuplay.ru')]


class ChangeResourceCommand:

    __keyboard = None

    def __init__(self, bot):
        self.bot = bot
        self.user_input = False

    @property
    def keyboard(self):
        return self.__keyboard

    @keyboard.setter
    def keyboard(self, keys: list):
        self.__keyboard = [[{'text': key.name, 'callback_data': key.value}] for key in keys if key is Key]

    def execute(self, message):
        pass

    def change_bot_resource(self, resource_name):
        self.bot.resource = resource_name