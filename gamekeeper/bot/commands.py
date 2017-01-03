
class ChangeBotResourceCommand:

    __keyboard = None
    user_input = False
    id = '/resource'

    def __init__(self, bot):
        self.bot = bot
        self.keyboard = [(r,v.resource_name) for r,v in bot.resources.items()]

    @property
    def keyboard(self):
        return self.__keyboard

    @keyboard.setter
    def keyboard(self, keys_data):
        self.__keyboard = [[{'text': key[0], 'callback_data': key[1]}] for key in keys_data]

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
            self.bot.active_command= False
