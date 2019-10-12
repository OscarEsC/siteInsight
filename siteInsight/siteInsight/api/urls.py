from django.urls import path
# import api/views.py
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]