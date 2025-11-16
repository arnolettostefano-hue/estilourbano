from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.index, name='index'),
    path('suggestions/', views.suggestions, name='suggestions'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/success/', views.cart_success, name='cart_success'),
]
