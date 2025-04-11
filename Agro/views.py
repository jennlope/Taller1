#MongoDB library
from pymongo import MongoClient
from bson.objectid import ObjectId

from django.shortcuts import render,redirect
from .models import Agro



'''
#MongoDB server client conection
client = MongoClient("mongodb+srv://AgroMerc:AgroMerc2023@cluster0.5elomeg.mongodb.net")

#Database
db = client["AgroMerc"]

#Collections
colClients=db['Clientes']
colProducts = db['Productos']
colPurchases = db['Compras']
colCar=db['BuyerCar']
'''

# Patrón observador

# Clase base para los observadores
class Observer:
    def on_user_created(self, user_data):
        pass

# Cuando un usuario se crea, se notifica a todos los observadores registrados
class EmailBienvenida(Observer):
    def on_user_created(self, user_data):
        print(f"[Correo] Bienvenido {user_data['name']}! Se envió un correo a {user_data['email']}")

class UserRegistro(Observer):
    def on_user_created(self, user_data):
        print(f"[Log] Usuario {user_data['userName']} registrado con éxito.")

# El publicador
class UserRegistrationNotifier:
    def __init__(self):
        self.observers = []

    def register(self, observer):
        self.observers.append(observer)

    def notify(self, user_data):
        for observer in self.observers:
            observer.on_user_created(user_data)


# Abstracciones para el acceso a la base de datos. 
# Estas funciones ahora actúan como interfaces. 

def get_db():
    #MongoDB server client conection
    client = MongoClient("mongodb+srv://AgroMerc:AgroMerc2023@cluster0.5elomeg.mongodb.net")
    #Database
    return client["AgroMerc"]

def get_collection(name):
    return get_db()[name]

def get_col_clients():
    return get_collection("Clientes")

def get_col_products():
    return get_collection("Productos")

def get_col_purchases():
    return get_collection("Compras")

def get_col_car():
    return get_collection("BuyerCar")

# User
userOnline = {}


# Create your views here.

def signIn(request):
    exist=False
    correctPassword=False
    trySignIn=False
    inSignIn=False
    if request.method == 'POST':
        trySignIn=True
        userName=str(request.POST['userName'])
        password=str(request.POST['password'])
        # verify if user exist and the password is correct
        
        # Devuelve la colección de clientes de la base de datos
        colClients = get_col_clients()

        # Busca un usuario en la base de datos y verifica que su campo de username sea igual al ingresado o que el campo email sea igual al username.
        user = colClients.find_one({"$or": [{"userName": userName}, {"email": userName}]}) #El operador "$or" devuelve documentos que cumplen al menos una de las condiciones especificadas en la lista.

        if user:
            exist = True
            if password == user['password']:
                correctPassword = True
                inSignIn = True
                userActive(user)

    context={"existAccount":exist, 
             "correctPassword":correctPassword,
             "inSignIn":inSignIn,
             "trySignIn":trySignIn
    }
    
    return render(request,'signIn.html',context)
        
                
def signUp(request):
    #boolean data
    existCedula=False
    existEmail=False
    existUserName=False
    registered=False
    dataError=False
    textName=""
    textSurname=""
    textCedula=""
    textPhoneNumber=""
    textEmail=""
    textUserName=""
    textPassword=""
    trySignUp=False
    if request.method == 'POST':
        trySignUp=True
        name=str(request.POST['name'])
        surnames=str(request.POST['surnames'])
        cedula=str(request.POST['cedula'])
        phoneNumber=str(request.POST['phoneNumber'])
        email=str(request.POST['email'])
        userName=str(request.POST['userName'])
        password=str(request.POST['password'])
        userType=str(request.POST.get('userType'))
        if name == "":
            textName="Por favor ingrese su nombre"
            dataError=True
        if surnames == "":
            textSurname="Por favor ingrese su(s) Apellido(s)"
            dataError=True
        if cedula == "":
            textCedula="Por favor ingrese su cédula"
            dataError=True
        if phoneNumber=="":
            textPhoneNumber="Por favor ingrese su número de teléfono"
            dataError=True
        if email=="":
            textEmail="Por favor ingrese su correo electrónico"
            dataError=True
        if userName=="":
            textUserName="Por favor ingrese su nombre de usuario"
            dataError=True
        if password=="":
            textPassword="Por favor ingrese una contraseña"
            dataError=True
        if not dataError:
            colClients = get_col_clients()
            existing = colClients.find_one({
                "$or": [
                    {"userName": userName},
                    {"cedula": cedula},
                    {"email": email}
                ]
            })

            if existing:
                if existing['userName'] == userName:
                    existUserName = True
                    textUserName = f"El usuario {userName} ya existe, intente uno diferente"
                if existing['cedula'] == cedula:
                    existCedula = True
                    textCedula = "La cédula ya se encuentra registrada"
                if existing['email'] == email:
                    existEmail = True
                    textEmail = f"El correo electrónico {email} ya se encuentra registrado"

            else:
                # Registro exitoso
                registered = True
                user_data = {
                    "name": name,
                    "surnames": surnames,
                    "cedula": cedula,
                    "phoneNumber": phoneNumber,
                    "email": email,
                    "userName": userName,
                    "password": password,
                    "userType": userType
                }
                inserted = colClients.insert_one(user_data)

                request.session['user_id'] = str(inserted.inserted_id)

                notifier = UserRegistrationNotifier()
                notifier.register(EmailBienvenida())
                notifier.register(UserRegistro())
                notifier.notify(user_data)


    context={"textName":textName,"textSurName":textSurname,"textCedula":textCedula,"textEmail":textEmail,
             "textPhoneNumber":textPhoneNumber,"textUserName":textUserName,"textPassword":textPassword,
             "existUserName":existUserName,"existCedula":existCedula,"existEmail":existEmail,
             "registered":registered,"trySignUp":trySignUp}
    return render(request,'signUp.html',context) #verificar para no montar nada en blanco

def agroMerc(request):
    context={"userActive":False}
    return render(request,'AgroMerc.html',context)

def mainMenu(request):
    global userOnline
    user=userOnline
    colProducts = get_col_products()
    productsListName = list(colProducts.find())
    seller = False
    #verify if is seller
    if user['userType'] == 'seller':
        seller = True
    # Obtener la categoría seleccionada desde el GET
    selected_category = request.GET.get('category', None)
    
    if selected_category:
        if selected_category != 'nothing':
            # Filtrar productos por la categoría seleccionada
            productsListName = list(colProducts.find({"categories": selected_category}))
        elif selected_category=='nothing':
            productsListName = list(colProducts.find())
        
    #look for products list
    context={"name":user['name'],'surnames':user['surnames'],
             "cedula":user['cedula'],"phoneNumber":user['phoneNumber'],
             "email":user['email'],"userName":user['userName'],
             "password":user['password'],"seller":seller,
             "productsListName":productsListName,'category':selected_category}
    return render(request,'mainMenu.html',context)

def purchase(request):
    global userOnline
    user = userOnline
    colCar = get_col_car()
    if request.method == 'POST':
        action = request.POST.get('action')
        productId = request.POST.get('product_id')
        productId2 = request.POST.get('product_id2')
        product = searchProduct(productId, productId2)
        seller = searchSeller(str(productId))
        try:
            quantityOrdered = int(request.POST.get('quantityOrdered'))
            available_quantity = int(product['maxQuantity'])

            # Validar cantidad ANTES de cualquier acción
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
            
            
            if quantityOrdered > available_quantity:
                context = {
                    "product": product,
                    "quantityOrdered": quantityOrdered,
                    "user": user,
                    "seller": seller,
                    "error": True,
                    "errorMessage": f"La cantidad solicitada ({quantityOrdered}) excede el límite ({available_quantity})."
                }
                return render(request, 'purchase.html', context)

            # Solo si la cantidad es válida, proceder:
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
            print("Value Error")
            return redirect('mainMenu')

    # Si no hay POST, render por defecto
    return render(request, 'purchase.html', {"purchaseMade": False})


def madeAPurchase(request):
    global userOnline
    user = userOnline
    purchaseMade = False
    purchaseCancel = False
    colCar = get_col_car()

    if request.method == 'POST':
        status = request.POST.get('purchaseStatus')
        if status == 'yes':
            purchaseMade = True
            # Obtener todos los productos en el carrito del usuario
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

                # Actualizar stock y registrar compra
                possiblePurchase(
                    product['id2'],
                    str(int(product['maxQuantity']) - quantityOrdered),
                    seller['cedula']
                )
                addPurchase(data)

            # ✅ Vaciar carrito de este usuario
            colCar.delete_many({'idBuyer': user['cedula']})

        elif status == 'no':
            purchaseCancel = True

    context = {
        "purchaseMade": purchaseMade,
        "purchaseCancel": purchaseCancel
    }
    return render(request, 'purchaseMade.html', context)


    
def home(request):
    search_term = request.GET.get('searchProduct', '')
    category_filter = request.GET.get('category', 'Todos')

    if category_filter == 'Todos':
        agros = Agro.objects.filter(title__icontains=search_term)
    else:
        agros = Agro.objects.filter(title__icontains=search_term, category=category_filter)

    categories = Agro.objects.values_list('category', flat=True).distinct()
    categories = ['Todos'] + list(categories)  # Add "Todos" to the list of categories

    context = {
        'searchTerm': search_term,
        'agros': agros,
        'categories': categories,
        'selected_category': category_filter,
    }
    return render(request, 'home.html', context)


def about(request):
    #return HttpResponse('<h1>Welcome to About page</h1>')
    return render(request, 'about.html')

def addProduct(request):
    global userOnline
    user=userOnline
    colProducts = get_col_products()    
    productAdded=False
    if request.method=='POST':
        productAdded=True
        productName=str(request.POST.get("productName"))
        specificName=str(request.POST["specificName"])
        unit=str(request.POST.get('unit'))
        maxQuantity=str(request.POST['maxQuantity'])
        minQuantity=str(request.POST['minQuantity'])
        id2v=id2(user['cedula'])
        category = addCategories(productName)
        data={"name":productName,"specificName":specificName,
              "maxQuantity":maxQuantity,"minQuantity":minQuantity,
              "unit":unit,"seller":user['name']+' '+user['surnames'],
              "id":user['cedula'],"id2":id2v,'categories':category}
        #add to database
        colProducts.insert_one(data)
        if productAdded:
            return redirect('mainMenu')
        productAdded=True
    context={"productAdded":productAdded}
    return render(request, 'AddProducts.html',context)

def myProducts(request):
    global userOnline
    user = userOnline
    colProducts = get_col_products()
    myProductsList=[]
    if request.method=='POST':
        action = request.POST.get('action')
        productId = request.POST.get('product_id')
        if action == 'delete':
            #delete product
            colProducts.delete_one({'_id': ObjectId(productId)})
            return redirect('myProducts')
        elif action == 'edit':
            product = colProducts.find_one({'_id': ObjectId(productId)})
            product['product_id'] = str(product['_id'])
            return render(request,'editProducts.html',{'product':product})
        elif action == 'update':
            #update product
            updatedData={
                        'name':request.POST.get('product_name'),
                        'specificName':request.POST.get('product_specificName'),
                        'maxQuantity':request.POST.get('max_quantity'),
                        'minQuantity':request.POST.get('min_quantity'),
                        'unit':str(request.POST.get('unit')),
                        'seller':request.POST.get('product_seller'),
                        'id':request.POST.get('product_id1'),
                        'id2':request.POST.get('product_id2')}
            print(updatedData)
            colProducts.update_one({'_id': ObjectId(productId)}, {'$set': updatedData})
            return redirect('myProducts')
    for product in colProducts.find():
        if product['id'] == user['cedula']:
            # Añadir una nueva clave para evitar el guion bajo
            product['product_id'] = str(product['_id'])
            myProductsList.append(product)
    context={"myProductsList":myProductsList}
    return render(request,'myProducts.html',context)
    

def buyerCar(request):
    global userOnline
    user = userOnline
    products=searchCar(user['cedula'])
    context={'products':products}
    return render(request,'buyercar.html',context)

    """
    auxiliary functions to the views functions implements
    """
def userActive(user):
    global userOnline
    userOnline = user
    
def searchProduct(id,id2):
    colProducts = get_col_products()
    product=colProducts.find({"id":id,"id2":id2})
    return(product[0])

def searchSeller(cedula):
    colClients = get_col_clients()
    search=colClients.find({"cedula":cedula})
    for seller in search:
        return seller
    
def searchCar(idBuyer):
    colCar = get_col_car()
    search = colCar.find({'idBuyer':idBuyer})
    return search
    
def possiblePurchase(id2,newValue,idSeller):
    colProducts = get_col_products()
    colProducts.update_one({"id":idSeller,"id2":id2},{"$set":{"maxQuantity":newValue}})
    
def addPurchase(data):
    colPurchases = get_col_purchases()
    colPurchases.insert_one(data)
    
def id2(id):
    id2Value=0
    colProducts = get_col_products()
    for product in colProducts.find({"id":id}):
        id2Value=product['id2']
    id2Value=str(int(id2Value)+1)
    return id2Value

def addCategories(productName):
    category={
        'Aguacate': ['Frutas tropicales', 'Fuentes de fibra'],
        'Banano': ['Frutas tropicales', 'Fuentes de fibra'],
        'Brócoli': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Café': ['Granos'],
        'Cebolla_Cabezona': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Cebolla_Larga': ['Hortalizas', 'Verduras crucíferas', 'Fuentes de fibra'],
        'Coliflor': ['Hortalizas', 'Verduras crucíferas'],
        'Frijol': ['Legumbres', 'Fuentes de fibra','Granos'],
        'Guayaba': ['Frutas tropicales', 'Fuentes de fibra'],
        'Lechuga': ['Hortalizas', 'Fuentes de fibra'],
        'Limón': ['Frutas tropicales', 'Cítricos'],
        'Lulo': ['Frutas tropicales', 'Cítricos'],
        'Maíz': ['Legumbres', 'Fuentes de fibra','Granos'],
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
            categories=category[productName]
            return categories
    
def handleCarAction(request):
    global userOnline
    user = userOnline
    colCar = get_col_car()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'purchase':
            # Procesar la compra
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
                
                # Actualizar stock
                possiblePurchase(
                    product['id2'],
                    str(int(product['maxQuantity']) - int(item['quantityOrdered'])),
                    seller['cedula']
                )
                # Registrar compra
                addPurchase(data)
        
        # Vaciar el carrito en ambos casos (compra o cancelación)
        colCar.delete_many({'idBuyer': user['cedula']})
        
        return redirect('mainMenu')
    
    return redirect('buyerCar')