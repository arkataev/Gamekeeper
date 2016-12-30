from abc import ABCMeta, abstractmethod, abstractproperty


class absResource(metaclass=ABCMeta):


    @abstractproperty
    def resource_name(self):
        pass

    @abstractmethod
    def search(self, query):
        pass

    # @abstractmethod
    # def show_actions(self):
    #     pass


