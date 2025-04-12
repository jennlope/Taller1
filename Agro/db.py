from .singleton import MongoConnectionSingleton

# Obtener instancia única de la base de datos
db = MongoConnectionSingleton().get_db()

# Funciones para acceder a cada colección
def get_col_clients():
    return db["Clientes"]

def get_col_products():
    return db["Productos"]

def get_col_purchases():
    return db["Compras"]

def get_col_car():
    return db["BuyerCar"]