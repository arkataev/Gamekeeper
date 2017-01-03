from abc import ABCMeta, abstractmethod, abstractproperty


class absResource(metaclass=ABCMeta):




    @abstractmethod
    def search(self, query):
        pass

    # @abstractmethod
    # def show_actions(self):
    #     pass


