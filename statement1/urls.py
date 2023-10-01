from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('add/', InsertUser, name='insertuser'),
    path('delete/<id>', DeleteUser, name='deleteuser'),
    path('export/', export_to_pdf, name='exportuser'),
]