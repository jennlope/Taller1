from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    #return HttpResponse('<h1>Welcome to AgroMerc</h1>')
    #return render(request, 'home.html')
    return render(request, 'home.html', {'name':'Jennifer'})

def about(request):
    #return HttpResponse('<h1>Welcome to About page</h1>')
    return render(request, 'about.html')

def addProduct(request):
    return render(request, 'AddProducts.html')