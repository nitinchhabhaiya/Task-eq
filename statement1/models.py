from django.db import models

# Create your models here.

class UserProfile(models.Model):
    username = models.CharField(max_length=255,unique=True)
    user_email = models.EmailField(max_length=255,unique=True)
    password = models.CharField(max_length=500)
    added = models.DateField(auto_now_add=True, blank=True, null=True)
    updated = models.DateField(auto_now=True, blank=True, null=True)
    
    def __str__(self):
        return self.username

GENDER_LIST = (
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
)
class UserInfo(models.Model):
    user_id = models.ForeignKey(UserProfile,on_delete=models.CASCADE,blank=True,null=True)
    date_of_birth = models.DateField(auto_now=False,blank=True,null=True)
    mobile = models.CharField(default="", max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GENDER_LIST, blank=True, null=True)
    address = models.TextField(default="", blank=True, null=True)
    added = models.DateField(auto_now_add=True, blank=True, null=True)
    updated = models.DateField(auto_now=True, blank=True, null=True)
    
    
class BlockedIPAddress(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    request_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.ip_address