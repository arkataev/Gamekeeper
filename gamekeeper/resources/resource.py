from abc import ABCMeta, abstractmethod


class absResource(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def search(self, query):
        pass

    @abstractmethod
    def show_actions(self):
        pass

