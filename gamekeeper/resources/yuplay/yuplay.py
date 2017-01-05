from lxml import html
import requests
import re
from urllib.parse import urlencode
from gamekeeper.resources.resource import absResource, Game


class YuPlay(absResource):

    __url = 'http://yuplay.ru'
    resource_name = 'Yuplay.ru'

    def __init__(self):
        self.__games = []
        self.__current_page = 1
        self.__total_pages = 1

    def get_options(self):
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
            try:
                # html-блок со списком игр
                games_list = resource.body.find_class('games-box')[0]
            except IndexError:
                # Ошибка если не удалось обнаружить блок с играми на странице результатов поиска
                return 'Ничего найти не удалось:('
            self.games.append(self.__collect_games(games_list))
        return self

    def __collect_games(self, games_list):
        clean_price = re.compile(r"\d+\s\d+|\d+")
        return [Game(
            name=child.xpath('a')[0].find('span').text.strip(),
            link=self.__url + child.xpath('a')[0].attrib['href'],
            price=clean_price.findall(child.find_class('price')[0].text_content()))
         for child in games_list.getchildren()]

    def count_results(self):
        return sum(map(lambda page: len(page),self.games))

    def __get_data(self, query, page):
        suffix = '/products/search/'
        return requests.get(self.__url + suffix, headers={
            'user-aget':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
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

    def __repr__(self):
        info = "<b>{}</b>\n".format(self.resource_name)
        for page in self.games:
            for game in page:
                try:
                    price = game.price[0].split()[1]
                except IndexError:
                    price = game.price[0]
                info+= "<a href='{}' target='_blank'>{}</a> - {}руб.\n".format(game.link, game.name, price)
        info += "\t"
        return info
