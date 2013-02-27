# -*- coding: utf-8 -*-
import datetime, hashlib, json

from django.db import models
from django.core.cache import cache

from abc import ABCMeta, abstractmethod, abstractproperty

from core.cached_model import ModelWithCaching
from core import debug_file

from django.utils import timezone;

now = timezone.now;

class Flags(ModelWithCaching):
    key = models.CharField(primary_key=True, max_length = 32);
    value = models.CharField(max_length = 128);
    deadline = models.DateTimeField();
    life_secs = models.IntegerField(default = 60);

    @classmethod
    def factory(cls, key):
	obj = Flags._factory(key);
	isinstance(obj, Flags);
	if obj.deadline < now():
	    obj.delete();
	    raise models.ObjectDoesNotExist;
	return obj;
	    
    
    @classmethod
    def create(cls, key,val,life_secs):
        obj = Flags(key = key, value = json.dumps(val),life_secs = life_secs, deadline = now() + datetime.timedelta(seconds = life_secs));
        obj.save();
        return obj;
    
    @property
    def Value(self):
        return json.loads(self.value);
    @Value.setter
    def Value(self, val):
        self.value = json.dumps(val);
        self.deadline = now() + datetime.timedelta(seconds = self.life_secs);


class SnsDriver(object):
    """абстрактный Класс-драйвер соцсети"""
    __metaclass__=ABCMeta;

    def register_user_level(self, uid, level):
	pass;
    
    @abstractmethod
    def get_image(self, uid, size = (50,50)):
        """Получить картинку из соцсети"""
        pass;

    
    @abstractmethod
    def get_url(self, uid):
        """Получить юрл пользователя из соцсети"""
        pass;

    @abstractmethod
    def get_name(self, uid):
        pass;
    
    @abstractmethod
    def check_signature(self, request):
        """Проверить подпись"""
        return False;
    
    
    
class SnsType(ModelWithCaching):
    """типы соцсетей"""
    id = models.CharField(max_length = 16, null = False, primary_key = True);
    name = models.CharField(max_length = 128, null = False);
    sec_key = models.CharField(max_length = 128, null = False);
    
    def __unicode__(self):
	return self.name;
    

class SnsUser(ModelWithCaching):
    """Пользователь соц.сети"""
    
    id = models.AutoField(primary_key = True);
    uid = models.CharField(max_length = 128, null = False, help_text = u"Идентификатор пользователя в соцсети");
    sns_type = models.ForeignKey(SnsType);
    
    name = models.CharField(max_length = 128, default = '');
    img = models.CharField(max_length = 128, null = True, blank = True, default = None);
    url = models.CharField(max_length = 128, null = True, blank = True, default = None);
    email = models.CharField(max_length = 128, null = True, blank = True, default = None);
    #api_url = models.CharField(max_length = 128, null = True, blank = True, default = None);
    
    suspended = models.BooleanField(null = False, default = False, help_text = u'Признак блокировки пользователя');
    
    session_id = models.CharField(default = '', max_length = 64, help_text = u'ид сессии');
    login_time = models.DateTimeField(default = now());
    
    _use_cache = False;
    
    def __unicode__(self):
	return "%s [%s]" % (self.name, self.uid);

    def __int__(self):
	return self.id;
    
    @classmethod
    def factory(cls, id):
	obj = SnsUser._factory(id);
	isinstance(obj, SnsUser);
        return obj;    
    
    @classmethod
    def check_user(cls, vid, sns):
	"""Проверим зарегин ли пользователь"""
	try:
	    user = cls.objects.get(uid = vid, sns_type_id = sns);
	    user.refresh_img();
	except models.ObjectDoesNotExist:
	    return False;
	return SnsUser.factory(user.id);
    
    @classmethod
    def register(cls, vid, sns):
	"""зарегить пользователя"""
	sns_type = SnsType.factory(sns);
	user = SnsUser(uid = vid, sns_type = sns_type);
	Driver = user._get_class();
	user.name = Driver.get_name(vid);
	user.img = Driver.get_image(vid);
	user.url = Driver.get_url(vid);
	user.save_in();
	return SnsUser.factory(user.id);

    def report_user_level(self, level):
	drv = self._get_class();
	return drv.report_user_level(self.uid, level);
	
    
    def get_app_freands(self):
	drv = self._get_class();
	return drv.get_app_freands(self.uid);
    
    def get_freands(self):
	drv = self._get_class();
	return drv.get_freands(self.uid);
    
    def is_session(self, request):
	session_id = request.REQUEST.get('session_id', '');
	return session_id != '';
    
    def start_session(self):
        """создает сессию и возвращает ее идшник"""
	self.login_time = now();
        sid = hashlib.md5("%s%s%s" % (self.uid, self.sns_type_id, self.login_time)).hexdigest();
        self.session_id = sid;
        self.save_up();
        return sid;

    def check_auth(self, session_id):
	if session_id != self.session_id:
	    pass;
	    #debug_file((session_id != self.session_id, session_id, self.session_id));
        return session_id == self.session_id;
    
    def _get_class(self):
        """Получить класс-драйвер соцсети с которым будем работать"""
        if self.sns_type_id == 'vk':
            from sns_user.vk.models import SNSVkDriver;
            return SNSVkDriver();
        if self.sns_type_id == 'mail':
            from sns_user.mail.models import SNSMailDriver;
            return SNSMailDriver();
        if self.sns_type_id == 'odkl':
            from sns_user.odkl.models import SNSOdklDriver;
            return SNSOdklDriver();
            
    def sendNotify(self, notify_text):
	Driver = self._get_class();
	Driver.send_notify(self.uid, notify_text);

    def send_notifies(self, uids, notify_text):
	Driver = self._get_class();
	Driver.send_notifies(uids, notify_text);
    
    @property
    def Url(self):
        """Юрл страници пользователя"""
        if self.url is None:
            Driver = self._get_class();
            self.url = Driver.get_url(self.uid);
        return self.url;

    @property
    def Img(self):
        """Юрл страници пользователя"""
	if self.img == "#":
	    self.img = None;
        if self.img is None:
            Driver = self._get_class();
            self.img = Driver.get_image(self.uid);
	#if self.sns_type_id == 'odkl':
	#    self.img = '/kazino/data/images/freands_photo.jpg';
        return self.img;
    
    def refresh_img(self):
	Driver = self._get_class();
        self.img = Driver.get_image(self.uid);
	self.save_up();
        
    def was_today(self):
	"""заходил ли игрок сегодня"""
	return self.login_time.date() == now().date();


    @property
    def Online(self):
        try:
            flag = Flags.factory('online:%d' % self.id);
        except ObjectDoesNotExist:
            return False;
        return flag.Value;
    @Online.setter
    def Online(self, value):
        key = 'online:%d' % self.id;
        if value:
            try:
                flag = Flags.factory(key);
                flag.Value = True;
                flag.save_up();
            except ObjectDoesNotExist:
                flag = Flags.create(key, True, 600);
        else:
            try:
                flag = Flags.factory(key);
                flag.delete();
            except ObjectDoesNotExist:
                pass;
        return;
    
    