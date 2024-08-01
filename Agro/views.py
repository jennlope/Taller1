from django.shortcuts import render
from django.http import HttpResponse

from .models import Agro
# Create your views here.

def home(request):
    #return HttpResponse('<h1>Welcome to AgroMerc</h1>')
    #return render(request, 'home.html')
    searchTerm = request.GET.get('searchProduct')
    if searchTerm:
        agros = Agro.objects.filter(title__icontains=searchTerm)
    else:
        agros = Agro.objects.all()
    return render(request, 'home.html', {'searchTerm':searchTerm,'agros':agros})

def about(request):
    #return HttpResponse('<h1>Welcome to About page</h1>')
    return render(request, 'about.html')