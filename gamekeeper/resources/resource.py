from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple


# Шаблон для создания опции ресурса
Option = namedtuple('Option', ['name', 'message', 'value'])
# Модель записи игры для удобного хранения
Game = namedtuple("Game", ('name', 'link', 'price'))

class absResource(metaclass=ABCMeta):

    @abstractmethod
    def search(self, query):
        pass

    @abstractmethod
    def get_options(self) -> dict:
        pass

    @abstractmethod
    def count_results(self) -> int:
        pass


