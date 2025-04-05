import uuid
from functools import lru_cache
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.signing import Signer, BadSignature

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


class Session(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  year = models.PositiveSmallIntegerField()
  name = models.CharField(max_length=128)
  pricelist = models.JSONField()

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
  def order_count(self):
    return self.ordered_count() / self.blanks_count() * 100

  @lru_cache
  def last_order_time(self):
    return self.order_set.filter(deleted=None, ordered__isnull=False).order_by('-ordered').only('ordered').first().ordered


trans = str.maketrans(
  'абвгдежзиклмнопрстуфхцчшщэюя',
  'abvgdejziklmnoprstyfx_cw_qu_',
)

def upload_blank(order, filename):
  album = order.album
  return f'blanks/{album.sessoin.year}_{album.session.name}/{album.sh}/{album.shyear}{album.group.lower().translate(trans)}/{uuid.uuid4()}/{filename}'


class Order(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  ordered = models.DateTimeField(null=True)
  album = models.ForeignKey(Album, on_delete=models.DO_NOTHING)
  json = models.JSONField()
  blank = models.FileField(upload_to=upload_blank)
