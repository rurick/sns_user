# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from sns_user.models import SnsType, SnsUser

class SnsTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    
class SnsUserAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'uid', 'sns_type');
    search_fields = ['uid'];
    
admin.site.register(SnsType, SnsTypeAdmin)
admin.site.register(SnsUser, SnsUserAdmin)
