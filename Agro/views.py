from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from bson.objectid import ObjectId
from .singleton import MongoConnectionSingleton
from .db import get_col_clients, get_col_products, get_col_purchases, get_col_car
from .registro import RegistroConMongo, SignInMongo
from .models import Agro

colClients = get_col_clients()
colProducts = get_col_products()
colPurchases = get_col_purchases()
colCar = get_col_car()

# Actividad 5 - CBV
# CBV - Sign In
class SignInView(View):
    def get(self, request):
        return render(request, 'signIn.html', {
            "existAccount": False,
            "correctPassword": False,
            "inSignIn": False,
        })

    def post(self, request):
        userName = request.POST.get('userName')
        password = request.POST.get('password')

        autenticador = SignInMongo()
        resultado = autenticador.autenticar(userName, password)

        if resultado.get("inSignIn"):
            user = resultado["user"]
            user["_id"] = str(user["_id"])
            request.session['user'] = user

        resultado["trySignIn"] = True
        resultado["userName"] = userName
        return render(request, 'signIn.html', resultado)

# CBV - Sign Up
class SignUpView(View):
    def get(self, request):
        return render(request, 'signUp.html', {})

    def post(self, request):
        data = {key: request.POST.get(key) for key in [
            "name", "surnames", "cedula", "phoneNumber",
            "email", "userName", "password", "userType"]}

        registro = RegistroConMongo()
        resultado = registro.registrar(data)
        resultado.update(data)
        return render(request, 'signUp.html', resultado)

# CBV - AgroMerc
class AgroMercView(TemplateView):
    template_name = 'AgroMerc.html'

    def get_context_data(self, **kwargs):
        return {"userActive": False}

# CBV - Main Menu
class MainMenuView(View):
    def get(self, request):
        user = request.session.get('user')
        if not user or 'userType' not in user:
            return redirect('signIn')

        seller = user['userType'] == 'seller'
        selected_category = request.GET.get('category')

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

# CBV - Purchase
class PurchaseView(View):
    def get(self, request):
        return render(request, 'purchase.html', {"purchaseMade": False})

    def post(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

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

# CBV - Made a Purchase
class MadeAPurchaseView(View):
    def post(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

        purchaseMade = False
        purchaseCancel = False
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

# CBV - Add Product
class AddProductView(View):
    def get(self, request):
        return render(request, 'AddProducts.html', {"productAdded": False})

    def post(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

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

# CBV - My Products
class MyProductsView(View):
    def get(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

        myProductsList = []
        for product in colProducts.find():
            if product['id'] == user['cedula']:
                product['product_id'] = str(product['_id'])
                myProductsList.append(product)

        return render(request, 'myProducts.html', {"myProductsList": myProductsList})

    def post(self, request):
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

# CBV - BuyerCar
class BuyerCarView(View):
    def get(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

        products = colCar.find({'idBuyer': user['cedula']})
        return render(request, 'buyercar.html', {'products': products})

# CBV - About
class AboutView(TemplateView):
    template_name = 'about.html'

# CBV - HandleCarAction
class HandleCarActionView(View):
    def post(self, request):
        user = request.session.get('user')
        if not user:
            return redirect('signIn')

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

        colCar.delete_many({'idBuyer': user['cedula']})
        return redirect('mainMenu')

    def get(self, request):
        return redirect('buyerCar')

#Aux
def searchProduct(id, id2):
    return colProducts.find_one({"id": id, "id2": id2})

def searchSeller(cedula):
    return colClients.find_one({"cedula": cedula})

def addPurchase(data):
    colPurchases.insert_one(data)

def possiblePurchase(id2, newValue, idSeller):
    colProducts.update_one({"id": idSeller, "id2": id2}, {"$set": {"maxQuantity": newValue}})

def id2(id):
    id2Value = 0
    for product in colProducts.find({"id": id}):
        id2Value = product['id2']
    return str(int(id2Value) + 1)

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
    return category.get(productName, [])