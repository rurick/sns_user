# -*- coding: utf-8 -*-
import urllib, urllib2, hashlib, json, random, time,datetime
from urlparse import urlparse
from django.utils import timezone, encoding
from django.utils.translation import gettext as _

from sns_user.models import SnsDriver, ModelWithCaching, models
from core import debug_file

from settings import VK_API_ID, VK_AUTH_KEY, VK_API_URL, VK_CONNECT_TIMEOUT

now = timezone.now;

class VkParams(ModelWithCaching):
    access_token = models.CharField(max_length = 128, null = True, blank = True); #https://api.vk.com/oauth/access_token?client_id=3183985&client_secret=rFt6EcoYTY3PInsHOrd7&grant_type=client_credentials
    
    @classmethod
    def factory(cls):
	obj = VkParams._factory(1);
	isinstance(obj, VkParams);
        return obj;    
    
    @classmethod
    def get_access_token(cls):
	obj = cls.factory();
	if not obj.access_token:
	    params = {'client_id' : VK_API_ID,
		      'client_secret' : VK_AUTH_KEY,
		      'grant_type' : 'client_credentials'
		      };
	    urllib.socket.setdefaulttimeout(15);
	    data = urllib.urlencode(params);
	    response = urllib.urlopen('https://api.vk.com/oauth/access_token', data);
	    answ = json.loads(response.read());
	    obj.access_token = answ['access_token'];
	    obj.save_up();
	return obj.access_token;
	    

class SNSVkDriver(SnsDriver):
    
    date = None;

    def report_user_level(self, uid, level):
	url = VK_API_URL; 
	params = {'api_id' : VK_API_ID,
	          'method' : 'secure.setUserLevel',
	          'format' : 'JSON',
                  'random' : random.randint(0,10000000000),
                  'timestamp' : int(time.mktime(datetime.datetime.now().timetuple())),
	          'uid' : uid,
	          'level' : level
	          };
	ss = u"".join([u"%s=%s" % (p,params[p]) for p in sorted(params)]);
	sig = hashlib.md5(encoding.smart_str(ss) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(15);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());
    
    def send_notifies(self, uids, notify_text):
	import urllib, urllib2, hashlib, json, time, datetime, random;
	url = VK_API_URL;
	params = {'api_id' : VK_API_ID,
                  'method' : 'secure.sendNotification',
                  'format' : 'JSON',
                  'uids' : uids,
                  'random' : random.randint(0,10000000000),
                  'timestamp' : int(time.mktime(datetime.datetime.now().timetuple())),
                  'message' : notify_text
                  };
	ss = u"".join([u"%s=%s" % (p,params[p]) for p in sorted(params)]);
	sig = hashlib.md5(encoding.smart_str(ss) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	params['message'] = encoding.smart_str(params['message']);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());	
	#debug_file(notify_text, datetime.datetime.now().strftime('%d-%m %H:%M'), True);
    
    def send_notify(self, uid, notify_text):
	import urllib, urllib2, hashlib, json, time, datetime, random;
	url = VK_API_URL;
	params = {'api_id' : VK_API_ID,
                  'method' : 'secure.sendNotification',
                  'format' : 'JSON',
                  'uids' : uid + ',',
                  'random' : random.randint(0,10000000000),
                  'timestamp' : int(time.mktime(datetime.datetime.now().timetuple())),
                  'message' : notify_text
                  };
	ss = u"".join([u"%s=%s" % (p,params[p]) for p in sorted(params)]);
	sig = hashlib.md5(encoding.smart_str(ss) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	params['message'] = encoding.smart_str(params['message']);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());	
    
    def get_info(self, vid):
        """получить инфу о юзере"""
	if self.date is not None:
	    return self.date;
	
	url = VK_API_URL;
	params = {'api_id' : VK_API_ID,
	          'method' : 'users.get',
	          'format' : 'JSON',
	          'uids' : vid,
	          'fields' : 'uid, first_name, last_name, nickname, sex, birthdate, city, country, timezone, photo, photo_medium, photo_big, photo_rec, connections'
	          };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(15);
	data = urllib.urlencode(params);
	response = urllib.urlopen(url, data);
	answ = json.loads(response.read());
	#assert False, answ;
	try:
	    self.date = answ['response'][0]['user'];
	    return answ['response'][0]['user'];
	except KeyError:
	    return None;
        
		
    def get_app_freands(self, vid, offset = 0, cnt = None):
	"""Получить друзей установивших приложение"""
	from sns_user.models import SnsUser;
	
	url = VK_API_URL;
	params = {'api_id' : VK_API_ID,
                  'method' : 'friends.get',
                  'format' : 'JSON',
                  'uid' : vid
                  };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(VK_CONNECT_TIMEOUT);
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
	                } for pl in SnsUser.objects.filter(sns_type = 'vk', uid__in = [str(r['uid']) for r in answ['response']]).order_by('id')];
	except KeyError:
	    players = [];
	return sorted(players, lambda p1,p2 : 1 if p1['name'] < p2['name'] else -1)[offset:cnt];		
	
    def get_freands(self, vid, offset = 0, cnt = None):
	"""Получить друзей """
	url = VK_API_URL;
	params = {'api_id' : VK_API_ID,
                  'method' : 'friends.get',
                  'format' : 'JSON',
	          'fields' : 'photo,photo_rec,first_name,last_name,uid,nickname, sex, birthdate',
                  'uid' : vid
                  };
	sig = hashlib.md5("".join(["%s=%s" % (p,params[p]) for p in sorted(params)]) + VK_AUTH_KEY).hexdigest();
	params['sig'] = sig;
	urllib.socket.setdefaulttimeout(VK_CONNECT_TIMEOUT);
	data = urllib.urlencode(params);
	try:
	    response = urllib.urlopen(url, data);
	except Exception as ex:
	    return [];
	    
	answ = json.loads(response.read());
	players = [{'url' : "http://vk.com/id%s" % r['user']['uid'],
	            'vid' : r['user']['uid'],
	            'img' : r['user']['photo_rec'] if urlparse(r['user']['photo_rec']).netloc[-11:] == 'userapi.com' else "/kazino/data/images/user_no_img.png",
	            'name' : u"%s %s" % (r['user']['first_name'], r['user']['last_name']),
	            } for r in answ['response']];
	return sorted(players, lambda p1,p2 : 1 if p1['name'] > p2['name'] else -1)[offset:cnt];


    

    def get_image(self, vid, size = (50,50)):
	from urlparse import urlparse;
	self.get_info(vid);
	return self.date['photo_rec'] if urlparse(self.date['photo_rec']).netloc[-11:] == 'userapi.com' else "/kazino/data/images/user_no_img.png";

    def get_url(self, vid, size = (50,50)):
	self.get_info(vid);
	return "http://vk.com/id%s" % vid;
    
    def get_nickname(self, vid, size = (50,50)):
	self.get_info(vid);
	return self.date['nickname'];
    
    def get_name(self, vid):
	self.get_info(vid);
	return "%s %s" % (self.date['first_name'], self.date['last_name']);
    
    def check_signature(self, request):
	from vk.settings import VK_AUTH_KEY;
	
	viewer_id = request.REQUEST.get('viewer_id', '0');
	api_id = request.REQUEST.get('api_id', 0);
	auth_key = request.REQUEST.get('auth_key', '');
	my_auth_key = hashlib.md5(str(api_id) + '_' + str(viewer_id) + '_' + VK_AUTH_KEY).hexdigest();
	return auth_key == my_auth_key;	