# -*- coding: utf-8 -*-
import urllib, urllib2, hashlib, json, urlparse

from sns_user.models import SnsDriver

from settings import VK_API_ID, VK_AUTH_KEY, VK_API_URL, VK_CONNECT_TIMEOUT

class SNSVkDriver(SnsDriver):
    
    date = None;

    def sendNotify(self, notify_id):
        pass;
    
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
	            'img' : r['user']['photo_rec'] if urlparse(r['user']['photo_rec']).netloc[-11:] == 'userapi.com' else "/data/images/user_no_img.png",
	            'name' : u"%s %s" % (r['user']['first_name'], r['user']['last_name']),
	            } for r in answ['response']];
	return sorted(players, lambda p1,p2 : 1 if p1['name'] > p2['name'] else -1)[offset:cnt];


    

    def get_image(self, vid, size = (50,50)):
	from urlparse import urlparse;
	self.get_info(vid);
	return self.date['photo_rec'] if urlparse(self.date['photo_rec']).netloc[-11:] == 'userapi.com' else "/data/images/user_no_img.png";

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