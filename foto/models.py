import uuid
from functools import lru_cache
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.signing import Signer, BadSignature
from django.urls import reverse

# try:
#   import zoneinfo
# except ImportError:
#   from backports import zoneinfo

# zone = zoneinfo.ZoneInfo('Asia/Krasnoyarsk')
signer = Signer()

class User(AbstractUser):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4)
  company = models.ForeignKey('Company', on_delete=models.DO_NOTHING, null=True)


class Company(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  company = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, related_name='companies')
  name = models.CharField(max_length=128)
  city = models.CharField(max_length=128)
  address = models.CharField(max_length=512)
  tel = models.CharField(max_length=11)
  mail = models.EmailField()
  site = models.CharField(max_length=128)
  pricelist = models.JSONField()
  visible = models.BooleanField(default=True)
  active = models.BooleanField(default=True)


class Job(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
  user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
  prints = models.JSONField()
  status = models.PositiveSmallIntegerField()
  payed = models.DateTimeField()


class Pricelist(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  name = models.CharField(max_length=64)
  '''
    'formats': {
      'f10':    {'ru': 'Фото 10х15',   'price': 400,  'en': '10x15'},
      "f15":    {"ru": "Фото 15х23",   "price": 450,  'en': '15x23'},
      "f20":    {"ru": "Фото 20х30",   "price": 500,  'en': '20x30'},
      "f30":    {"ru": "Фото 30х42",   "price": 600,  'en': '30x42'},
      "m10":    {"ru": "Магнит 10х15", "price": 500,  'en': 'm10x15'},
      "m15":    {"ru": "Магнит 15х23", "price": 600,  'en': 'm15x23'},
      "pill":   {"ru": "Подушка",      "price": 1200, 'en': 'podushka'},
      "mug":    {"ru": "Кружка",       "price": 800,  'en': 'krujka'},
      "tshirt": {"ru": "Футболка",     "price": 1200, 'en': 'futbolka'},
      "tsize":  {"ru": "Обхват груди", "price": 0,    'en': 'razmer'},
      "book":  {"ru": "Фотокнига (обложка - коллаж, разворот - виньетка)", "price": 1500,    'en': 'kniga'},
      "set":  {"ru": "Выгодный комплект (портрет, коллаж и виньетка 20х30)", "price": 1200,    'en': 'komplekt'},
    },
  '''
  formats = models.JSONField()
  '''
    'themes': {
      'port': {
        'ru': 'Портрет',
        "blank_img_style": "aspect-ratio:726/527;background-position:6.3% 3.2%;background-size:166%;transform:rotate(90deg);margin:13.7% 0;border-radius:0;",
        'formats': [
          "f10", "f15", "f20", "f30", "m10", "m15", "pill", "mug", "tshirt", "tsize"
        ],
      },
      'vint': {
        'ru': 'Виньетка',
        "blank_img_style": "aspect-ratio:726/527;background-size:166%;background-position:6.3% 48.5%;",
        'formats':[
          "f15", "f20", "f30", "m10", "m15", "pill", "mug", "tshirt", "tsize"
        ],
      },
      'coll': {
        'ru': 'Коллаж',
        'blank_img_style': 'aspect-ratio:726/527;background-size:166%;background-position:6.3% 94%;',
        'formats':[
          "f15", "f20", "f30", "m10", "m15", "pill", "mug", "tshirt", "tsize"
        ],
      },
      'all': {
        'ru': 'Все фото',
        'blank_img_style': 'aspect-ratio:1205/1795;background-size:100%;background-position:center;',
        'formats':[
          "book", "set"
        ],
      },
    },
  '''
  themes = models.JSONField()
  '''
    'bonus': {
      "text": "При заказе от %(sum)s₽ - электронный портрет в подарок!",
      "success": "Электронный портрет в подарок!!",
      "sum": 2000,
    },
  '''
  bonus = models.JSONField()


class Session(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  year = models.PositiveSmallIntegerField()
  name = models.CharField(max_length=128)
  pricelist = models.ForeignKey(Pricelist, on_delete=models.DO_NOTHING, null=True)

  def __str__(self):
    return f'{self.year}_{self.name}'


class Album(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  closed = models.DateTimeField(null=True)
  session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
  sh = models.CharField(max_length=3)
  shyear = models.PositiveSmallIntegerField()
  group = models.CharField(max_length=16)

  def __str__(self):
    return f'{self.session}__{self.name}'

  def get_json(self):
    return {
      'id': self.id,
      'name': self.name,
      'ses_id': self.session_id,
      'ses': f'{self.session}',
      'sh': self.sh,
      'yr': self.shyear,
      'gr': self.group,
      'cls': f'{self.shyear}{self.group}',
      'sign': self.sign(),
      'signed_url': self.sign(),
      'blanks_count': self.blanks_count(),
      'ordered_count': self.ordered_count(),
      'order_progress': self.order_progress(),
      'closed': self.closed is not None and self.closed or self.deleted is not None and self.deleted,
      'is_closed': self.closed is not None or self.deleted is not None,
    }

  @lru_cache
  def sign(self):
    return signer.sign(str(self))

  @property
  def name(self):
    return f'{self.sh}_{self.shyear}{self.group}'

  def money_table_url(self):
    adr, _, code = self.sign().partition(':')
    return f'{code}/{adr}/money_table/'

  @lru_cache
  def ordered_count(self):
    return self.order_set.filter(ordered__isnull=False, deleted=None).count()

  @lru_cache
  def blanks_count(self):
    return self.order_set.filter(deleted=None).count()

  @lru_cache
  def order_progress(self):
    blanks_count = self.blanks_count()
    if not blanks_count: return 0
    return self.ordered_count() / blanks_count * 100

  @lru_cache
  def last_order_time(self):
    return self.order_set.filter(deleted=None, ordered__isnull=False).order_by('-ordered').only('ordered').first().ordered #.astimezone(zone)


trans = str.maketrans(
  'абвгдежзиклмнопрстуфхцчшщэюя',
  'abvgdejziklmnoprstyfxCcwWquY',
)

def upload_blank(order, filename):
  album = order.album
  return f'blanks/{album.session.year}_{album.session.name}/{album.sh}/{album.shyear}{album.group.lower().translate(trans)}/{uuid.uuid4()}/{filename}'


class Order(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  ordered = models.DateTimeField(null=True)
  album = models.ForeignKey(Album, on_delete=models.DO_NOTHING)
  json = models.JSONField(null=True, default=dict)
  blank = models.FileField(upload_to=upload_blank)
  imgname = models.CharField(max_length=64, default='')

  def __str__(self):
    return f'{self.album}__{self.blank.name.rsplit("/", 1)[-1].rsplit(".", 1)[0]}'

  def url(self):
    return reverse('order', kwargs={'sign': signer.sign(f'{self.album}__{self.imgname}'), 'id': self.id})






