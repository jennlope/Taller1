#Actividad 5 - Aplicacion Singleton 1/2
from pymongo import MongoClient

class MongoConnectionSingleton:
    _instance = None

    def __init__(self):
        if not MongoConnectionSingleton._instance:
            MongoConnectionSingleton._instance = MongoClient("mongodb+srv://AgroMerc:AgroMerc2023@cluster0.5elomeg.mongodb.net")

    def get_client(self):
        return MongoConnectionSingleton._instance

    def get_db(self):
        return self.get_client()["AgroMerc"]