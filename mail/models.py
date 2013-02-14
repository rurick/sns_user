# -*- coding: utf-8 -*-
import urllib, urllib2, hashlib, json, random, time,datetime
from urlparse import urlparse
from django.utils import timezone, encoding
from django.utils.translation import gettext as _

from sns_user.models import SnsDriver, ModelWithCaching, models
from core import debug_file

from settings import MAIL_API_ID, MAIL_AUTH_KEY, MAIL_API_URL, MAIL_CONNECT_TIMEOUT

now = timezone.now;

class SNSMailDriver(SnsDriver):
    
    date = None;

    def report_user_level(self, uid, level):
	pass;
    
    def send_notifies(self, uids, notify_text):
	import urllib, urllib2, hashlib, json, time, datetime, random;
	url = MAIL_API_URL;
	params = {'app_id' : MAIL_API_ID,
                  'method' : 'notifications.send',
                  'uids' : uids,
                  'secure' : 1,
                  'format' : 'json',
                  'text' : text
                  };
	ss = u"".join([u"%s=%s" % (p,params[p]) for p in sorted(params)]);
	sig = hashlib.md5(encoding.smart_str(ss) + MAIL_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	params['message'] = encoding.smart_str(params['message']);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());	
	#debug_file(notify_text, datetime.datetime.now().strftime('%d-%m %H:%M'), True);
    
    def send_notify(self, uid, notify_text):
	import urllib, urllib2, hashlib, json, time, datetime, random;
	url = MAIL_API_URL;
	url = MAIL_API_URL;
	params = {'app_id' : MAIL_API_ID,
                  'method' : 'notifications.send',
                  'uids' : uid + ',',
                  'secure' : 1,
                  'format' : 'json',
                  'text' : text
                  };
	ss = u"".join([u"%s=%s" % (p,params[p]) for p in sorted(params)]);
	sig = hashlib.md5(encoding.smart_str(ss) + MAIL_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	params['message'] = encoding.smart_str(params['message']);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());	
    
    def get_info(self, vid):
        """получить инфу о юзере"""
	if self.date is not None:
	    return self.date;
	
	url = MAIL_API_URL;
	params = {'app_id' : MAIL_API_ID,
                  'method' : 'users.getInfo',
                  'uid' : vid,
                  'secure' : 1,
                  'format' : 'json',
                  'uids' : vid
                  };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + MAIL_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(15);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());
	try:
	    self.date = answ[0];
	    return answ[0];
	except KeyError:
	    return None;
        
		
    def get_app_freands(self, vid, offset = 0, cnt = None):
	"""Получить друзей установивших приложение"""
	from sns_user.models import SnsUser;
	
	url = MAIL_API_URL;
	params = {'app_id' : MAIL_API_ID,
                  'method' : 'friends.getAppUsers',
                  'uid' : vid,
                  'secure' : 1,
                  'ext' : 1,
                  'format' : 'json'
                  };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + MAIL_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(MAIL_CONNECT_TIMEOUT);
	data = urllib.urlencode(params);
	try:
	    response = urllib.urlopen(url, data);
	except Exception as ex:
	    return [];
	    
	answ = json.loads(response.read());
	try:
	    players = [{'id' : pl.id,
	                'url' : pl.url,
	                'vid' : pl.uid,
	                'img' : pl.Img,
	                'image' : pl.Img,
	                'name' : pl.name,
	                } for pl in SnsUser.objects.filter(sns_type = 'mail', uid__in = [str(r['uid']) for r in answ]).order_by('id')];
	except KeyError:
	    players = [];
	return sorted(players, lambda p1,p2 : 1 if p1['name'] < p2['name'] else -1)[offset:cnt];		
	
    def get_freands(self, vid, offset = 0, cnt = None):
	"""Получить друзей """
	url = MAIL_API_URL;
	params = {'app_id' : MAIL_API_ID,
                  'method' : 'friends.getAppUsers',
                  'uid' : vid,
                  'secure' : 1,
                  'ext' : 1,
                  'format' : 'json'
                  };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + MAIL_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(MAIL_CONNECT_TIMEOUT);
	data = urllib.urlencode(params);
	try:
	    response = urllib.urlopen(url, data);
	except Exception as ex:
	    return [];
	    
	answ = json.loads(response.read());
	players = [{'url' : r['link'],
	            'vid' : r['uid'],
	            'img' : r['pic_small'] if urlparse(r['pic_small']).netloc == 'avt.appsmail.ru' else "/kazino/data/images/user_no_img.png",
	            'name' : u"%s %s" % (r['first_name'], r['last_name']),
	            } for r in answ];
	return sorted(players, lambda p1,p2 : 1 if p1['name'] > p2['name'] else -1)[offset:cnt];


    

    def get_image(self, vid, size = (50,50)):
	from urlparse import urlparse;
	self.get_info(vid);
	return self.date['pic_small'] if urlparse(self.date['pic_small']).netloc == 'avt.appsmail.ru' else "/kazino/data/images/user_no_img.png";

    def get_url(self, vid, size = (50,50)):
	self.get_info(vid);
	return self.date['link'];
    
    def get_nickname(self, vid, size = (50,50)):
	self.get_info(vid);
	return self.date['nick'];
    
    def get_name(self, vid):
	self.get_info(vid);
	return "%s %s" % (self.date['first_name'], self.date['last_name']);
    
    def check_signature(self, request):
	from mail.settings import MAIL_AUTH_KEY;
	auth_key = request.REQUEST.get('auth_key', '');
	params = {};
	get_items = request.REQUEST.items();
	for get_it in get_items:
	    if get_it[0] != 'sig':
		params[get_it[0]] = get_it[1];
	params = "".join(["%s=%s" % (p,params[p]) for p in sorted(params)]);
	my_auth_key = hashlib.md5(params + MAIL_AUTH_KEY).hexdigest();
	return auth_key == my_auth_key;	