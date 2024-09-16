#MongoDB library
from pymongo import MongoClient

from django.shortcuts import render


#MongoDB server client conection
client = MongoClient("mongodb+srv://AgroMerc:AgroMerc2023@cluster0.5elomeg.mongodb.net")

#Database
db = client["AgroMerc"]

#Collections
colClients=db['Clientes']
colProducts = db['Productos']
colPurchases = db['Compras']


# Create your views here.

def mainMenu(request):
    query = {"userName": "McLovin", "password": "McLovin69"}
    user = colClients.find_one(query)
    # Verificar si se encontró el usuario
    if user:
        print("Usuario encontrado:", user)
    else:
        print("Usuario no encontrado.")
    productsListName = []
    seller = False
    #verify if is seller
    if user['userType'] == 'seller':
        seller = True
    #look for products list
    for product in colProducts.find():
        #add product at list to be shown
        productsListName.append(product)
    context={"name":user['name'],'surnames':user['surnames'],
             "cedula":user['cedula'],"phoneNumber":user['phoneNumber'],
             "email":user['email'],"userName":user['userName'],
             "password":user['password'],"seller":seller,
             "productsListName":productsListName}
    return render(request,'mainMenu.html',context)