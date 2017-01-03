import requests
import re
from operator import attrgetter
from gamekeeper.resources.resource import absResource, Option
from collections import namedtuple

class Plati(absResource):

    __url = 'http://www.plati.com/api/search.ashx'
    resource_name = 'Plati.ru'
    __rating = 200

    def __init__(self):
        self.__current_page = 1
        self.__sellers = []

    def search(self, query):
        if self.sellers: self.sellers = []
        # Результаты поиска
        found_games = self.__get_sellers(query)
        if not found_games:
            return 'Ничего найти не удалось:('

        # Модель записи игры для удобного хранения
        Game = namedtuple("Game", ('name', 'link', 'price'))
        # Паттерн на поиск товара по ключевом слову
        regex_search = self.__key_words(query)
        # Паттерн на исключение товара из поиска
        regex_except = self.__excluded_words(['ps3', 'ps4', 'xbox'])
        # Фильтруем найденные товары по критериям
        matched_good_sellers = self.__filter_sellers([
            lambda seller: not regex_except.search(seller['name']) and regex_search.search(seller['name']),
            self.__is_good_seller
        ], found_games)
        # Группируем полученные товары по продавцу
        sellers_dict= {}
        for good_seller in matched_good_sellers:
            sellers_dict.setdefault(good_seller['seller_name'], []).append(Game(name=good_seller['name'],
                                                                                price=good_seller['price_rur'],
                                                                                link=good_seller['url']))
        # Добавляем каждого продавца и его игры в общий список продавцов
        for seller in sellers_dict:
            self.sellers.append({'seller_name': seller, 'games': sorted(sellers_dict[seller], key=attrgetter('price'))})
        # Сортируем продавцов в общем списке по цене самой дешевой игры имеющейся у продавца
        self.sellers.sort(key=lambda seller: seller['games'][0].price)
        return self

    def __filter_sellers(self, rules, sellers):
        """
        Рекурсивно применяет правила для фильтрации объектов в списке. Результат фильтрации первого
        правила является входящим списком для фильтрации по второму правилу и т.д.

        :param rules:       Список функций применяемых для фильтрации
        :param sellers:     Список, который нужно отфильтровать
        :return:            Отфильтрованный список
        """
        f_sellers = filter(rules[0], sellers)
        return f_sellers if len(rules) == 1 else self.__filter_sellers(rules[1:], f_sellers)

    def get_options(self):
        return {
            'set_rating': Option(name='Рейтинг продавца', value=lambda r: setattr(self, 'rating', r),
                                 message='Введите число от 0 до 1000')
        }

    def __get_sellers(self, query):
        page = items = 1
        sellers = []
        while items:
            r = requests.get(self.__url, params={'query': query, 'response': 'json', 'pagenum': page})
            items = r.json()['items']
            if items: sellers.extend(items)
            page += 1
        return sellers

    def __is_good_seller(self, seller):
        params = {
            'count_negativeresponses': lambda i: not i,
            'count_returns': lambda i: not i,
            'seller_rating': lambda i: int(i) >= self.rating,
        }
        return all([params[param](seller[param]) for param in params.keys()])

    def __repr__(self):
        info = "<b>{}</b>\n".format(self.resource_name)
        for seller in self.sellers:
            info += "<b>{}</b>\n".format(seller['seller_name'])
            for game in seller['games']:
                info += "<a href='{}' target='_blank'>{}</a> - {}руб.\n\t".format(game.link, game.name, game.price)
        return info

    @staticmethod
    def __excluded_words(words):
        regex = '|'.join(words)
        return re.compile(r".*({})".format(regex), re.IGNORECASE)

    @staticmethod
    def __key_words(query):
        _query_regex = ['({})'.format(word) for word in str(query).split(' ')]
        return re.compile("{}".format(r'.*?\b'.join(_query_regex)), re.IGNORECASE)

    @property
    def sellers(self):
        return self.__sellers

    @property
    def rating(self):
        return int(self.__rating)

    @sellers.setter
    def sellers(self, value):
        self.__sellers = value

    @rating.setter
    def rating(self, value):
        assert str(value).isdigit(), ValueError('Значение рейтинга должно быть числом')
        assert 0 < int(value) < 1000, ValueError('Значение должно быть между 0 и 1000')
        self.__rating = value
