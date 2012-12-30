# -*- coding: utf-8 -*-
import os
from django.http import HttpResponse

def receiver_html(request):
    f = file(os.path.dirname(__file__) + '/receiver.html', 'r');
    return HttpResponse(f.read());