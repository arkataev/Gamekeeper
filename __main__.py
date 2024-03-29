from gamekeeper import Gamekeeper, default_message_handler
import re


if __name__ == '__main__':
    try:
        with open('.env') as env_file:
            env = env_file.read()
            params = re.findall(r"(?P<name>.*?)=(?P<value>.*)", env)
    except FileNotFoundError:
        exit(u'.env not found')
    for param in params: setattr(Gamekeeper, param[0], param[1])
    Gamekeeper.run(default_message_handler)