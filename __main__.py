from gamekeeper import Bot, default_message_handler
import re

if __name__ == '__main__':
    with open('.env') as env_file:
        env = env_file.read()
        params = re.findall(r"(?P<name>.*?)=(?P<value>.*)", env)
    for param in params: setattr(Bot, param[0], param[1])
    Bot.run(default_message_handler)
