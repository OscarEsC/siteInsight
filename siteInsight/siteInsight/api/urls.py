from django.urls import path
from . import views

#Redirecciones dentro de la app api
urlpatterns = [
    path('', views.index, name='index'),
    path('update_config/', views.update_config, name='update_config'),
]