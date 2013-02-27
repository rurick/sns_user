# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^/receiver.html$', 'sns_user.mail.views.receiver_html'),

)
