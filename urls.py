# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^/mail', include('sns_user.mail.urls')),
    url(r'^/odkl', include('sns_user.odkl.urls')),

)
