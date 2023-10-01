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

regex = "([a-zA-Z0-9]+(?:[._+-][a-zA-Z0-9]+)*)@([a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*[.][a-zA-Z]{2,})"
# Create your views here.

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


# def ExportUser(request):
#     context = UserInfo.objects.all().select_related('user_id')
#     return render_pdf("export-pdf.html",{'context':context})

# def render_pdf(template_path, context):
#     template = get_template(template_path)
#     html = template.render(context)
#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

#     if not pdf.err:
#         response = HttpResponse(result.getvalue(), content_type='application/pdf')
#         response['Content-Disposition'] = 'filename="exported_table.pdf"'
#         return response


def export_to_pdf(request):
    # Your code to retrieve table data goes here (replace this example data)
    table_data = []
    table_headar = ['Id','Username','Email','Password','Birth date','Mobile','Gender','Address']
    table_data.append(table_headar)
    context = UserProfile.objects.all().values()
    i = 1
    for value in context:
        print(value['id'])
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