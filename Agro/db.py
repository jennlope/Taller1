from .singleton import MongoConnectionSingleton

#Instancia unica de la bd
db = MongoConnectionSingleton().get_db()

# Colections
def get_col_clients():
    return db["Clientes"]

def get_col_products():
    return db["Productos"]

def get_col_purchases():
    return db["Compras"]

def get_col_car():
    return db["BuyerCar"]