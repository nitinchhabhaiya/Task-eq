from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(UserInfo)
# admin.site.register(BlockedIPAddress)