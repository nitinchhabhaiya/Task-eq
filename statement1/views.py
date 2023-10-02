from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import *
from django.contrib import messages
from datetime import datetime
import re
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from hashlib import md5, pbkdf2_hmac
import base64, math, json, requests

from django.template.loader import get_template
from django.template import Context
from xhtml2pdf import pisa
from io import BytesIO

from django.http import FileResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import random

from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
import time

from django.conf import settings
import os
import PyPDF2
from PyPDF2 import PageObject
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

from django.core.files.storage import FileSystemStorage


regex = "([a-zA-Z0-9]+(?:[._+-][a-zA-Z0-9]+)*)@([a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*[.][a-zA-Z]{2,})"
# Create your views here.

@api_view(['GET'])
def statementApi(request):
    if request.method == 'GET':
        # Retrieve the Bearer token from the request header
        token = request.headers.get('Authorization')

        # Check if the Bearer token matches the expected value
        expected_token = "Bearer mf8nrqICaHYD1y8wRMBksWm7U7gLgXy1mSWjhI0q"
        if token == expected_token:
            usercount = list(UserProfile.objects.all().values_list('id', flat=True).order_by('id'))
            random_num =  random.randint(1, len(usercount))
            userlist = UserProfile.objects.get(id = usercount[random_num-1])
            userinfo = UserInfo.objects.get(user_id = userlist)
            
            context = {
                'username':userlist.username,
                'user_email':userlist.user_email,
                'password':userlist.password,
                'date_of_birth':userinfo.date_of_birth,
                'mobile':userinfo.mobile,
                'gender':userinfo.gender,
                'address':userinfo.address 
            }
            return JsonResponse({'message': 'Authentication successful!','data':context})
        else:
            return JsonResponse({'message': 'Authentication failed.'}, status=401)
    else:
        return JsonResponse({'message': 'Unsupported method.'}, status=405)

def index(request):
    context = UserInfo.objects.all().select_related('user_id')
    return render(request,"index.html",{'context':context})

def InsertUser(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        pwd = request.POST.get('pwd')
        dob = request.POST.get('dob')
        mobile = request.POST.get('mobile')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        
        if username and re.search(regex,email) and pwd and dob and mobile.isdigit() and len(mobile) == 10 and gender and address :
            # bdate = datetime.strptime(dob,"%d/%m/%Y")
            idExisxtes = UserProfile.objects.filter(Q(username = username) | Q(user_email = email)).exists()
            if idExisxtes:
                messages.error(request, 'Username Or Email already exist data!')
                return redirect("insertuser")
            
            UserProfile.objects.create(username=username,user_email=email,password=EncryptBase64(pwd))
            last_id = UserProfile.objects.all().last()
            UserInfo.objects.create(user_id =last_id, date_of_birth=dob, mobile=mobile, gender=gender, address=address)
            return redirect("index")
            
        messages.error(request, 'Invalid data!')
        return redirect("insertuser")
    return render(request,"add-user.html")

def DeleteUser(request,id):
    UserProfile.objects.filter(id=id).delete()
    return redirect("index")


def export_to_pdf(request):
    table_data = []
    table_headar = ['Id','Username','Email','Password','Birth date','Mobile','Gender','Address']
    table_data.append(table_headar)
    context = UserProfile.objects.all().values()
    i = 1
    for value in context:
        UserList = UserInfo.objects.get(user_id = value['id'])
        output = [f'{i}',value['username'],value['user_email'],value['password'],UserList.date_of_birth,UserList.mobile,UserList.gender,UserList.address]
        table_data.append(output)
        i += 1

    # Create a PDF document
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="table_data.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    # Create a table
    data = []
    for row in table_data:
        data.append(row)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Build the PDF document
    elements = []
    elements.append(table)
    doc.build(elements)
    return response

def EncryptBase64(EncryptData):
    try:
        if EncryptData :
            ascii = EncryptData.encode("ascii")
            base64_bytes = base64.b64encode(ascii)
            base64_encrypt = base64_bytes.decode("ascii")
            return base64_encrypt
        error = "Invalid Parameter!!"
        return error
    except:
        error = "Invalid Parameter!!"
        return error
    
def DecryptBase64(DecryptData):
    try:
        if DecryptData :
            ascii = DecryptData.encode("ascii")
            base64_bytes = base64.b64decode(ascii)
            base64_decrypt = base64_bytes.decode("ascii")
            return base64_decrypt
        error = "Invalid Parameter!!"
        return error
    except:
        error = "Invalid Parameter!!"
        return error

def uploadPdf(request):
    if request.method == 'POST':
        pdf_file = request.FILES['pdf_file']
        if pdf_file:
            
            pdf_folder_path = os.path.join(settings.BASE_DIR,"media/pdf/")
            fs = FileSystemStorage(location = os.path.join(settings.BASE_DIR,"media/pdf/"))
            filename = fs.save(pdf_file.name, pdf_file)
            pdf_path = pdf_folder_path + filename
            
            # Add watermark to the PDF file
            watermark_pdf(pdf_path)

            output_pdf_path = pdf_path.replace('.pdf', '_watermarked_protected.pdf')
            PDFFile.objects.create(pdf_file=os.path.basename(output_pdf_path))
            return render(request, 'pdf-file.html',{'url':os.path.basename(output_pdf_path)})
        
    return render(request, 'pdf-file.html')

def watermark_pdf(pdf_file_path):
    # Add a watermark to the PDF file
    output_pdf_path = pdf_file_path.replace('.pdf', '_watermarked.pdf')

    pdf_reader = PyPDF2.PdfFileReader(open(pdf_file_path, 'rb'))
    pdf_writer = PyPDF2.PdfFileWriter()

    watermark = create_watermark_pdf()  # Create the watermark PDF

    for page_num in range(pdf_reader.getNumPages()):
        page = pdf_reader.getPage(page_num)
        # page.mergeTranslatedPage(page, 0, page.mediaBox.getHeight(), 1)
        page.mergePage(PageObject.createBlankPage(width=page.mediaBox.getWidth(), height=page.mediaBox.getHeight()))
        page.mergePage(watermark.getPage(0))
        pdf_writer.addPage(page)

    with open(output_pdf_path, 'wb') as output_pdf:
        pdf_writer.write(output_pdf)
        
    password = "12345"
    if password:
        password_protect_pdf(output_pdf_path, password)

def create_watermark_pdf():
    buffer = BytesIO()
    text = "eQuest Solution"
    pdf = canvas.Canvas(buffer)
    pdf.translate(inch, inch)
    pdf.setFillColor(colors.grey, alpha=0.6)
    pdf.setFont("Helvetica", 50)
    pdf.rotate(45)
    pdf.drawCentredString(400, 100, text)
    pdf.save()

    buffer.seek(0)
    watermark_pdf = PyPDF2.PdfFileReader(buffer)
    return watermark_pdf

def password_protect_pdf(pdf_file_path, password):
    # Make the PDF password-protected
    output_pdf_path = pdf_file_path.replace('.pdf', '_protected.pdf')

    pdf_reader = PyPDF2.PdfFileReader(open(pdf_file_path, 'rb'))
    pdf_writer = PyPDF2.PdfFileWriter()

    for page_num in range(pdf_reader.getNumPages()):
        page = pdf_reader.getPage(page_num)
        pdf_writer.addPage(page)

    pdf_writer.encrypt(user_pwd=password, use_128bit=True)
    with open(output_pdf_path, 'wb') as output_pdf:
        pdf_writer.write(output_pdf)
