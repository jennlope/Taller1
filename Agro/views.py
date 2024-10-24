#MongoDB library
from pymongo import MongoClient
from bson.objectid import ObjectId

from django.shortcuts import render,redirect




#MongoDB server client conection
client = MongoClient("mongodb+srv://AgroMerc:AgroMerc2023@cluster0.5elomeg.mongodb.net")

#Database
db = client["AgroMerc"]

#Collections
colClients=db['Clientes']
colProducts = db['Productos']
colPurchases = db['Compras']
colCar=db['BuyerCar']

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
        for users in colClients.find():
            if (userName==users['userName'] or userName == users['email']):
                exist=True
                #verify password
                if(password == users['password']):
                    #sign In succesfully
                    correctPassword=True
                    inSignIn=True
                    userActive(users)
                    break
    context={"existAccount":exist, "correctPassword":correctPassword,
             "inSignIn":inSignIn,"trySignIn":trySignIn}
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
            for client in colClients.find():
                if client['userName'] == userName:
                    existUserName=True
                if client['cedula'] == cedula:
                    existCedula=True
                if client['email'] == email:
                    existEmail=True
            if(not existUserName and not existCedula and not existEmail ):
                registered = True
                #save data in database
                data={"name":name,"surnames":surnames,"cedula":cedula,
                    "phoneNumber":phoneNumber,"email":email,
                    "userName":userName,"password":password,
                    "userType":userType}
                colClients.insert_one(data)
            if(existUserName):
                textUserName="El usuario "+userName+ " ya existe, intente uno diferente"
            if(existCedula):
                textCedula="La cédula ya se encuentra registrada"
            if(existEmail):
                textEmail="El correo electrónico "+email+" ya se encuentra registrado"
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
    purchaseMade=False
    global userOnline
    user=userOnline
    if request.method=='POST':
        action = request.POST.get('action')
        productId=request.POST.get('product_id')
        productId2=request.POST.get('product_id2')
        product=searchProduct(productId,productId2)
        seller=searchSeller(str(productId))
        try:
            quantityOrdered=int(request.POST.get('quantityOrdered'))
            if action=='addToCar':
                data={'nameProduct':product['name'],'productSpecificName':product['specificName'],
                      'productId2':product['id2'], 'nameSeller':product['seller'], 
                      'idBuyer':user['cedula'],'idSeller':seller['cedula'],
                      'quantityOrdered':quantityOrdered}
                print(data)
                colCar.insert_one(data)
                return redirect('mainMenu')
            if action=='purchase':
                context={"buyed":purchaseMade,"product":product,
                        "quantityOrdered":quantityOrdered,"user":user,"seller":seller}
                return render(request,'purchase.html',context)
        except ValueError:
                print("Value Error")
                return redirect('mainMenu')
    context={"purchaseMade":purchaseMade}
    return render(request,'purchase.html',context)

def madeAPurchase(request):
    global userOnline
    user=userOnline
    purchaseMade=False
    purchaseCancel=False
    if request.method=='POST':
        for key, value in request.POST.items():
            print(value)
            if key.startswith('purchaseMade_'):
                purchaseMade=True
                values=key.split('_')
                quantityOrdered=int(values[1])
                product=searchProduct(values[3],values[2])
                seller=searchSeller(values[3])
                data={"seller":seller['name'],"sellerCedula":product['id'],"productName":product['name']+" "+product['specificName'],"id2Product":product['id2'],"buyer":user['name']+" "+user['surnames'],"quantitySold":quantityOrdered}
                possiblePurchase(product['id2'],str(int(product['maxQuantity'])-quantityOrdered),seller['cedula'])
                addPurchase(data)
            else:
                purchaseCancel=True
    context={"purchaseMade":purchaseMade,"purchaseCancel":purchaseCancel}             
    return render(request,'purchaseMade.html',context)
    
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
    product=colProducts.find({"id":id,"id2":id2})
    return(product[0])

def searchSeller(cedula):
    search=colClients.find({"cedula":cedula})
    for seller in search:
        return seller
    
def searchCar(idBuyer):
    search = colCar.find({'idBuyer':idBuyer})
    return search
    
def possiblePurchase(id2,newValue,idSeller):
    colProducts.update_one({"id":idSeller,"id2":id2},{"$set":{"maxQuantity":newValue}})
    
def addPurchase(data):
    colPurchases.insert_one(data)
    
def id2(id):
    id2Value=0
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
    
