from abc import abstractmethod

from peewee import Database


class DatabaseSource:

    @abstractmethod
    def createDatabase(self)->Database:
        pass