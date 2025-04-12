"""
URL configuration for AgroMerc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Agro.views import (SignInView, SignUpView, AgroMercView, MainMenuView, PurchaseView, MadeAPurchaseView, AddProductView, MyProductsView, BuyerCarView, AboutView, HandleCarActionView)

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SignInView.as_view(), name='signIn'),
    path('signUp', SignUpView.as_view(), name='signUp'),
    path('agroMerc', AgroMercView.as_view(), name='agroMerc'),
    path('mainMenu', MainMenuView.as_view(), name='mainMenu'),
    path('purchase', PurchaseView.as_view(), name='purchase'),
    path('madeAPurchase', MadeAPurchaseView.as_view(), name='madeAPurchase'),
    path('about', AboutView.as_view(), name='about'),
    path('addProduct', AddProductView.as_view(), name='addProduct'),
    path('myProducts', MyProductsView.as_view(), name='myProducts'),
    path('buyercar', BuyerCarView.as_view(), name='buyerCar'),
    path('handle-car-action/', HandleCarActionView.as_view(), name='handleCarAction'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
