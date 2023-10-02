from django.urls import path
from .views import *

urlpatterns = [
    # USER Details
    path('', index, name='index'),
    # USER Add
    path('add/', InsertUser, name='insertuser'),
    # USER Delete
    path('delete/<id>', DeleteUser, name='deleteuser'),
    # USER Export
    path('export/', export_to_pdf, name='exportuser'),
    # API
    path('api/', statementApi, name='statementApi'),
    # PDF
    path('pdf/', uploadPdf, name='uploadpdf'),
    
]