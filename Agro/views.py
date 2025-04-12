from pymongo import MongoClient
from bson.objectid import ObjectId
from django.shortcuts import render, redirect
from .singleton import MongoConnectionSingleton
from .db import get_col_clients, get_col_products, get_col_purchases, get_col_car
from .registro import RegistroConMongo, SignInMongo
from .models import Agro

# Colecciones Mongo
colClients = get_col_clients()
colProducts = get_col_products()
colPurchases = get_col_purchases()
colCar = get_col_car()

def signIn(request):
    context = {
        "existAccount": False,
        "correctPassword": False,
        "inSignIn": False,
    }

    if request.method == 'POST':
        userName = request.POST.get('userName')
        password = request.POST.get('password')

        autenticador = SignInMongo()
        resultado = autenticador.autenticar(userName, password)

        if resultado.get("inSignIn"):
            request.session['user'] = resultado["user"]

        context.update(resultado)
        context["trySignIn"] = True
        context["userName"] = userName

    return render(request, 'signIn.html', context)

def signUp(request):
    context = {}
    if request.method == 'POST':
        data = {
            "name": request.POST.get("name"),
            "surnames": request.POST.get("surnames"),
            "cedula": request.POST.get("cedula"),
            "phoneNumber": request.POST.get("phoneNumber"),
            "email": request.POST.get("email"),
            "userName": request.POST.get("userName"),
            "password": request.POST.get("password"),
            "userType": request.POST.get("userType")
        }

        registro = RegistroConMongo()
        resultado = registro.registrar(data)
        context.update(resultado)
        context.update(data)

    return render(request, 'signUp.html', context)

def agroMerc(request):
    context = {"userActive": False}
    return render(request, 'AgroMerc.html', context)

def mainMenu(request):
    user = request.session.get('user')
    if not user or not isinstance(user, dict) or 'userType' not in user:
        return redirect('signIn')

    seller = user['userType'] == 'seller'
    selected_category = request.GET.get('category', None)

    if selected_category and selected_category != 'nothing':
        productsListName = list(colProducts.find({"categories": selected_category}))
    else:
        productsListName = list(colProducts.find())

    context = {
        "name": user['name'],
        "surnames": user['surnames'],
        "cedula": user['cedula'],
        "phoneNumber": user['phoneNumber'],
        "email": user['email'],
        "userName": user['userName'],
        "password": user['password'],
        "seller": seller,
        "productsListName": productsListName,
        "category": selected_category
    }
    return render(request, 'mainMenu.html', context)

def purchase(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    if request.method == 'POST':
        action = request.POST.get('action')
        productId = request.POST.get('product_id')
        productId2 = request.POST.get('product_id2')
        product = searchProduct(productId, productId2)
        seller = searchSeller(str(productId))
        try:
            quantityOrdered = int(request.POST.get('quantityOrdered'))
            available_quantity = int(product['maxQuantity'])
            min_quantity = int(product['minQuantity'])

            if quantityOrdered < min_quantity or quantityOrdered > available_quantity:
                context = {
                    "product": product,
                    "quantityOrdered": quantityOrdered,
                    "user": user,
                    "seller": seller,
                    "error": True,
                    "errorMessage": f"La cantidad debe estar entre {min_quantity} y {available_quantity}."
                }
                return render(request, 'purchase.html', context)

            if action == 'addToCar':
                data = {
                    'nameProduct': product['name'],
                    'productSpecificName': product['specificName'],
                    'productId2': product['id2'],
                    'nameSeller': product['seller'],
                    'idBuyer': user['cedula'],
                    'idSeller': seller['cedula'],
                    'quantityOrdered': quantityOrdered
                }
                colCar.insert_one(data)
                return redirect('mainMenu')

            elif action == 'purchase':
                context = {
                    "buyed": False,
                    "product": product,
                    "quantityOrdered": quantityOrdered,
                    "user": user,
                    "seller": seller,
                    "error": False
                }
                return render(request, 'purchase.html', context)

        except ValueError:
            return redirect('mainMenu')

    return render(request, 'purchase.html', {"purchaseMade": False})

def madeAPurchase(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    purchaseMade = False
    purchaseCancel = False

    if request.method == 'POST':
        status = request.POST.get('purchaseStatus')
        if status == 'yes':
            purchaseMade = True
            carItems = list(colCar.find({'idBuyer': user['cedula']}))
            for item in carItems:
                quantityOrdered = int(item['quantityOrdered'])
                product = searchProduct(item['idSeller'], item['productId2'])
                seller = searchSeller(item['idSeller'])

                data = {
                    "seller": seller['name'],
                    "sellerCedula": product['id'],
                    "productName": product['name'] + " " + product['specificName'],
                    "id2Product": product['id2'],
                    "buyer": user['name'] + " " + user['surnames'],
                    "quantitySold": quantityOrdered
                }

                possiblePurchase(product['id2'], str(int(product['maxQuantity']) - quantityOrdered), seller['cedula'])
                addPurchase(data)

            colCar.delete_many({'idBuyer': user['cedula']})

        elif status == 'no':
            purchaseCancel = True

    context = {
        "purchaseMade": purchaseMade,
        "purchaseCancel": purchaseCancel
    }
    return render(request, 'purchaseMade.html', context)

def addProduct(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    productAdded = False
    if request.method == 'POST':
        productName = str(request.POST.get("productName"))
        specificName = str(request.POST["specificName"])
        unit = str(request.POST.get('unit'))
        maxQuantity = str(request.POST['maxQuantity'])
        minQuantity = str(request.POST['minQuantity'])
        id2v = id2(user['cedula'])
        category = addCategories(productName)
        data = {
            "name": productName,
            "specificName": specificName,
            "maxQuantity": maxQuantity,
            "minQuantity": minQuantity,
            "unit": unit,
            "seller": user['name'] + ' ' + user['surnames'],
            "id": user['cedula'],
            "id2": id2v,
            "categories": category
        }
        colProducts.insert_one(data)
        return redirect('mainMenu')

    context = {"productAdded": productAdded}
    return render(request, 'AddProducts.html', context)

def myProducts(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    myProductsList = []
    if request.method == 'POST':
        action = request.POST.get('action')
        productId = request.POST.get('product_id')
        if action == 'delete':
            colProducts.delete_one({'_id': ObjectId(productId)})
            return redirect('myProducts')
        elif action == 'edit':
            product = colProducts.find_one({'_id': ObjectId(productId)})
            product['product_id'] = str(product['_id'])
            return render(request, 'editProducts.html', {'product': product})
        elif action == 'update':
            updatedData = {
                'name': request.POST.get('product_name'),
                'specificName': request.POST.get('product_specificName'),
                'maxQuantity': request.POST.get('max_quantity'),
                'minQuantity': request.POST.get('min_quantity'),
                'unit': str(request.POST.get('unit')),
                'seller': request.POST.get('product_seller'),
                'id': request.POST.get('product_id1'),
                'id2': request.POST.get('product_id2')
            }
            colProducts.update_one({'_id': ObjectId(productId)}, {'$set': updatedData})
            return redirect('myProducts')

    for product in colProducts.find():
        if product['id'] == user['cedula']:
            product['product_id'] = str(product['_id'])
            myProductsList.append(product)

    context = {"myProductsList": myProductsList}
    return render(request, 'myProducts.html', context)

def buyerCar(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    products = searchCar(user['cedula'])
    context = {'products': products}
    return render(request, 'buyercar.html', context)

def searchProduct(id, id2):
    product = colProducts.find({"id": id, "id2": id2})
    return product[0]

def searchSeller(cedula):
    search = colClients.find({"cedula": cedula})
    for seller in search:
        return seller

def searchCar(idBuyer):
    search = colCar.find({'idBuyer': idBuyer})
    return search

def possiblePurchase(id2, newValue, idSeller):
    colProducts.update_one({"id": idSeller, "id2": id2}, {"$set": {"maxQuantity": newValue}})

def addPurchase(data):
    colPurchases.insert_one(data)

def id2(id):
    id2Value = 0
    for product in colProducts.find({"id": id}):
        id2Value = product['id2']
    id2Value = str(int(id2Value) + 1)
    return id2Value

def about(request):
    return render(request, 'about.html')

def handleCarAction(request):
    user = request.session.get('user')
    if not user:
        return redirect('signIn')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'purchase':
            carItems = list(colCar.find({'idBuyer': user['cedula']}))
            for item in carItems:
                product = searchProduct(item['idSeller'], item['productId2'])
                seller = searchSeller(item['idSeller'])

                data = {
                    "seller": seller['name'],
                    "sellerCedula": product['id'],
                    "productName": product['name'] + " " + product['specificName'],
                    "id2Product": product['id2'],
                    "buyer": user['name'] + " " + user['surnames'],
                    "quantitySold": item['quantityOrdered']
                }

                possiblePurchase(
                    product['id2'],
                    str(int(product['maxQuantity']) - int(item['quantityOrdered'])),
                    seller['cedula']
                )
                addPurchase(data)

        # Vaciar carrito siempre
        colCar.delete_many({'idBuyer': user['cedula']})

        return redirect('mainMenu')

    return redirect('buyerCar')

def addCategories(productName):
    category = {
        'Aguacate': ['Frutas tropicales', 'Fuentes de fibra'],
        'Banano': ['Frutas tropicales', 'Fuentes de fibra'],
        'Brócoli': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Café': ['Granos'],
        'Cebolla_Cabezona': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Cebolla_Larga': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Coliflor': ['Hortalizas', 'Verduras crucíferas'],
        'Frijol': ['Legumbres', 'Fuentes de fibra', 'Granos'],
        'Guayaba': ['Frutas tropicales', 'Fuentes de fibra'],
        'Lechuga': ['Hortalizas', 'Fuentes de fibra'],
        'Limón': ['Frutas tropicales', 'Cítricos'],
        'Lulo': ['Frutas tropicales', 'Cítricos'],
        'Maíz': ['Legumbres', 'Fuentes de fibra', 'Granos'],
        'Mango': ['Frutas tropicales'],
        'Maracuyá': ['Frutas tropicales', 'Cítricos'],
        'Naranja': ['Frutas tropicales', 'Cítricos'],
        'Papa': ['Hortalizas', 'Tubérculos', 'Fuentes de fibra'],
        'Papaya': ['Frutas tropicales'],
        'Plátano': ['Frutas tropicales'],
        'Sandía': ['Frutas tropicales'],
        'Tomate': ['Hortalizas', 'Fuentes de fibra'],
        'Yuca': ['Hortalizas', 'Tubérculos', 'Fuentes de fibra'],
        'Zanahoria': ['Hortalizas', 'Tubérculos', 'Fuentes de fibra']
    }
    if productName in category:
        return category[productName]
