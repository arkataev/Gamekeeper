from lxml import html
import requests
import re
from urllib.parse import urlencode
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from operator import attrgetter


# Шаблон для создания опции ресурса
Option = namedtuple('Option', ('name', 'message', 'value'))
# Модель записи игры для удобного хранения
Game = namedtuple("Game", ('name', 'link', 'price'))

class AbsResource(metaclass=ABCMeta):

    @abstractmethod
    def search(self, query:str) -> object:
        pass

    @abstractmethod
    def get_options(self, option_name:str=None) -> Option or dict:
        pass

    @abstractmethod
    def count_results(self) -> int:
        pass


class YuPlay(AbsResource):
    __url = 'http://yuplay.ru'
    resource_name = 'Yuplay.ru'

    @property
    def page(self):
        return self.__current_page

    @page.setter
    def page(self, value):
        if value > self.total_pages:
            raise StopIteration
        self.__current_page = value

    @property
    def total_pages(self):
        return self.__total_pages

    @total_pages.setter
    def total_pages(self, value):
        self.__total_pages = int(value)

    @property
    def games(self):
        return self.__games

    @games.setter
    def games(self, value):
        self.__games = value

    def __init__(self):
        self.__games = []
        self.__current_page = 1
        self.__total_pages = 1

    def get_options(self, option_name=None):
        return {}

    def search(self, query):
        resources = []
        if self.games: self.games = []
        while True:
            try:
                content = self.__get_data(query, self.page)
                doc = self.__build_doc_tree_from_content(content)
                resources.append(doc)
                self.page += 1
            except StopIteration:
                break
        for resource in resources:
            found_games = resource.body.find_class('games-box')
            if not found_games: return
            self.games.append(self.__collect_games(found_games[0]))
        return self

    def count_results(self):
        return sum(map(lambda page: len(page), self.games))

    def __collect_games(self, games_list):
        clean_price = re.compile(r"\d+\s\d+|\d+")
        return [Game(
            name=child.xpath('a')[0].find('span').text.strip(),
            link=self.__url + child.xpath('a')[0].attrib['href'],
            price=clean_price.findall(child.find_class('price')[0].text_content()))
                for child in games_list.getchildren()]

    def __get_data(self, query, page):
        suffix = '/products/search/'
        return requests.get(self.__url + suffix, headers={
            'user-aget': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }, params=urlencode({'query': query, 'page': page})).content

    def __build_doc_tree_from_content(self, content):
        tree = html.fromstring(content)
        pagination = tree.body.find_class('pagination')
        # Количество страниц результатов поиска.
        # Определяется как количество абсолютных ссылок в пагинаторе, исключая 4 ссылки для относительной навигации
        # (дальше, назад, первая, последнияя) << <| 1, 2, 3 |> >>
        self.total_pages = len(pagination[0].getchildren()) - 4 if pagination else 1
        return tree

    def __repr__(self):
        info = "<b>{}</b>\n".format(self.resource_name)
        for page in self.games:
            for game in page:
                try:
                    price = game.price[0].split()[1]
                except IndexError:
                    price = game.price[0]
                info += "<a href='{}' target='_blank'>{}</a> - {}руб.\n".format(game.link, game.name, price)
        info += "\t"
        return info

class Plati(AbsResource):

    __url = 'http://www.plati.com/api/search.ashx'
    resource_name = 'Plati.ru'
    __rating = 200

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

    def __init__(self):
        self.__current_page = 1
        self.__sellers = []

    def search(self, query):
        if self.sellers: self.sellers = []
        # Результаты поиска
        found_games = self.__get_sellers(query)
        if not found_games: return
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

    def count_results(self):
        counter = map(lambda seller: len(seller['games']), self.sellers)
        return sum(counter)

    def get_options(self, option_name=None):
        options = {
            'set_rating': Option(name='Рейтинг продавца', value=lambda val: setattr(self, 'rating', val),
                                 message='Введите число от 0 до 1000')
        }
        return options.get(option_name, options)

    @staticmethod
    def __excluded_words(words):
        regex = '|'.join(words)
        return re.compile(r".*({})".format(regex), re.IGNORECASE)

    @staticmethod
    def __key_words(query):
        _query_regex = ['({})'.format(word) for word in str(query).split(' ')]
        return re.compile("{}".format(r'.*?\b'.join(_query_regex)), re.IGNORECASE)

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
                info += "<a href='{}' target='_blank'>{}</a> - {}руб.\n".format(game.link, game.name, game.price)
            info += "\t\n"
        return info
