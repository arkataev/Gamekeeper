import requests
import re
from operator import itemgetter
from gamekeeper.resources.resource import absResource


class Plati(absResource):
    __metaclass__ = absResource

    __url = 'http://www.plati.com/api/search.ashx'

    def search(self, query):
        # Словарь с результатами поиска
        sellers = {}
        # Паттерн на поиск
        _regex_search = self.__key_words(query)
        # Паттерн на исключение
        _regex_except = self.__excluded_words(['ps3', 'ps4', 'xbox'])
        # Фильтруем продавцов по критериям качества
        good_sellers = filter(self.__is_good_seller, self.__get_sellers(query))
        # Среди отобранных продавцов выбираем предложения, которые соответствуют запросу
        matched_good_sellers = filter(lambda seller:
                                      not _regex_except.search(seller['name'])
                                      and _regex_search.search(seller['name']), good_sellers)
        # Группируем полученные данные по продавцу
        for good_seller in matched_good_sellers:
            sellers.setdefault(good_seller['seller_name'], []).append((good_seller['name'],
                                                                       good_seller['price_rur'],
                                                                       good_seller['url']))
        # Сортируем продавцов по цене самого дешевого товара в их списке и возвращаем генератор
        return (self.__print_goods(seller, goods) for seller, goods in sorted(sellers.items(), key=Plati.__sort_by_price))

    @staticmethod
    def __sort_by_price(goods):
        """
        Возвращает самую низкую цену среди товаров продавца
        :param goods:
        :type goods: list
        :return:
        """
        # Создаем оператор для получения элементов из списков
        getter = itemgetter(1)
        # список кортежей с товарами продавца
        seller_goods = getter(goods)
        # сортируем товары продавца по возрастанию цены
        # TODO:: Заменить на min()
        seller_goods.sort(key=getter)
        # возвращаем оператор с ценой самого дешевого товара у продавца для использования при сортировке
        return getter(seller_goods[0])

    @staticmethod
    def __excluded_words(words):
        regex = '|'.join(words)
        return re.compile(r".*({})".format(regex), re.IGNORECASE)

    @staticmethod
    def __key_words(query):
        _query_regex = ['({})'.format(word) for word in str(query).split(' ')]
        return re.compile("{}".format(r'.*?\b'.join(_query_regex)), re.IGNORECASE)

    @staticmethod
    def __print_goods(seller, goods):
        info = "<b>{}:</b> \n".format(seller)
        for good in goods:
            info += "<a href='{}' target='_blank'>{}</a>- {}.руб\n".format(good[2], good[0], good[1])
        return info

    def __get_sellers(self, query):
        page = items = 1
        sellers = []
        while items:
            r = requests.get(self.__url, params={'query': query, 'response': 'json', 'pagenum': page})
            items = r.json()['items']
            sellers.extend(items)
            page += 1
        return sellers

    @staticmethod
    def __is_good_seller(seller):
        params = {
            'count_negativeresponses': lambda i: not i,
            'count_returns': lambda i: not i,
            'seller_rating': lambda i: int(i) >= 200,
        }

        return all([params[param](seller[param]) for param in params.keys()])