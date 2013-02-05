# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from sns_user.vk.models import VkParams

class VkParamsAdmin(admin.ModelAdmin):
    list_display = ('id','access_token')

admin.site.register(VkParams, VkParamsAdmin)
