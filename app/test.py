from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.server_api import ServerApi

import os


class Car:

    def __init__(self, brand, style):
        self.brand = brand
        self.style = style


if __name__ == "__main__":

    car = Car("honda", "sedan")
    breakpoint()
