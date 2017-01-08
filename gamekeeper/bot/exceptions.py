
class BotException(Exception):
    pass


class BotCommandException(BotException):

    def __init__(self, command, message):
        super().__init__(message)
        self.command = command
