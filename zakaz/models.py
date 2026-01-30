import uuid
from django.db import models
from django.db.models import Case, When, Value
# from django.contrib.auth.models import AbstractUser
from django.core.signing import Signer, BadSignature
from django.urls import reverse
from datetime import datetime
from re import compile as re

from django.utils.http import MAX_URL_LENGTH
from zakaz.utils import en

# try:
#   import zoneinfo
# except ImportError:
#   from backports import zoneinfo

# zone = zoneinfo.ZoneInfo('Asia/Krasnoyarsk')
signer = Signer()

def isonow():
    return datetime.now().replace(microsecond=0).isoformat()

# class User(AbstractUser):
#   id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#   company = models.ForeignKey('Company', on_delete=models.DO_NOTHING, null=True)


# class Company(models.Model):
#   created = models.DateTimeField(auto_now_add=True)
#   company = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, related_name='companies')
#   name = models.CharField(max_length=128)
#   city = models.CharField(max_length=128)
#   address = models.CharField(max_length=512)
#   tel = models.CharField(max_length=11)
#   mail = models.EmailField()
#   site = models.CharField(max_length=128)
#   pricelist = models.JSONField()
#   visible = models.BooleanField(default=True)
#   active = models.BooleanField(default=True)


# class Job(models.Model):
#   created = models.DateTimeField(auto_now_add=True)
#   company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
#   user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
#   prints = models.JSONField()
#   status = models.PositiveSmallIntegerField()
#   payed = models.DateTimeField()


class Pricelist(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)

  name    = models.CharField(max_length=64)
  formats = models.JSONField()
  themes  = models.JSONField()
  bonus   = models.JSONField()
  is_locked = models.BooleanField(default=False)

  def formats_dict(self):
      return {
          item['key']: item
          for item in (self.formats or [])
      }

  def as_json(self):
      return {
          'id': self.id,
          'name': self.name,
          'formats': self.formats_dict(),
          'themes': self.themes,
          'bonus': self.bonus,
          'locked': self.is_locked,
      }


class Session(models.Model):
  created   = models.DateTimeField(auto_now_add=True)
  updated   = models.DateTimeField(auto_now=True)
  deleted   = models.DateTimeField(null=True)

  year      = models.PositiveSmallIntegerField()
  name      = models.CharField(max_length=128)
  pricelist = models.ForeignKey(Pricelist, on_delete=models.DO_NOTHING, null=True)

  @property
  def sig(self):
      return str(self)

  def __str__(self):
    return f'{self.year}_{self.name}'

  def close_all(self, sh):
      # date = datetime.now()
      # self.album_set.filter(sh=sh).update(closed=date)
      for alb in self.album_set.filter(sh=sh):
          alb.close()

  def open_all(self, sh):
      self.album_set.filter(sh=sh).update(closed=None)


re_group = re(r'(\d+)?(\w)')


class School(models.Model):
    name    = models.CharField(max_length=64)
    slug    = models.CharField(max_length=3)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True)


class Album(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  closed  = models.DateTimeField(null=True)

  session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
  sh      = models.CharField(max_length=3)
  school  = models.ForeignKey(School, on_delete=models.DO_NOTHING, null=True)
  year    = models.PositiveSmallIntegerField()
  group   = models.CharField(max_length=16)

  def __str__(self):
    return f'{self.session}__{self.name}'

  def sign(self):
    return signer.sign(str(self))

  @classmethod
  def from_sign(cls, sign):
      try:
        unsigned = signer.unsign(sign)
        ses, _, alb = unsigned.partition('__')
        s_yr, _, s_nm = ses.partition('_')
        sh, _, gr = alb.partition('_')
        mo_gr = re_group.match(gr)
        return cls.objects.get(session__year=s_yr, session__name=s_nm, sh=sh, year=mo_gr[1], group=mo_gr[2])

      except BadSignature:
        return None

  @property
  def name(self):
    return f'{self.sh}_{self.year}{self.group}'

  # def money_table_url(self):
  #   adr, _, code = self.sign().partition(':')
  #   return f'{code}/{adr}/money_table/'

  def cache_progress(self):

      if self.is_closed:
          blanks = self.blank_set.filter(deleted=None).only('orders')
          total = 0
          ordered = 0
          for b in blanks:
              total += 1
              if b.orders and b.orders[-1].get('status') != -100:
                  ordered += 1

      else:      
          blanks = self.blank_set.filter(deleted=None).annotate(
              is_ordered=Case(
                  When(ordered__isnull=True, then=Value(False)),
                  default=Value(True),
              )
          ).values_list('is_ordered', flat=1)
          ordered = len([None for i in blanks if i])
          total = len(blanks)

      self.ordered = ordered
      self.blanks = total
      self.progress = 100 * ordered / total

  def last_order_time(self):
    return self.blank_set.filter(deleted=None, ordered__isnull=False).order_by('-ordered').only('ordered').first().ordered #.astimezone(zone)

  @property
  def is_deleted(self):
      return self.deleted is not None

  @property
  def is_closed(self):
      return self.closed is not None or self.deleted is not None

  def close(self):
      for b in self.blank_set.filter(deleted=None, ordered__isnull=False):
          if not b.order:
              continue
          b.archive_order()
      
      self.closed = datetime.now()
      self.save()

  def open(self):
      self.closed = None
      self.save()


def upload_blank(order, filename):
  album = order.album
  return f'blanks/{album.session.year}_{album.session.name}/{album.sh}/{album.year}{album.group.lower().translate(en)}/{uuid.uuid4()}/{filename}'


class Blank(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField(null=True)
  ordered = models.DateTimeField(null=True)

  album   = models.ForeignKey(Album, on_delete=models.DO_NOTHING)
  order   = models.JSONField(null=True, default=dict)
  orders  = models.JSONField(null=True, default=list)
  img     = models.FileField(upload_to=upload_blank)
  imgname = models.CharField(max_length=64, default='')
  name    = models.CharField(max_length=128, default='')

  def __str__(self):
      return f'{self.album}__{self.imgname}'

  def sign(self):
      return signer.sign(f'{self.album}__{self.imgname}__{self.id}')

  def is_ordered(self):
      return self.ordered is not None

  def is_cancelable(self):
      return self.ordered is not None and self.album.closed is None and self.album.deleted is None and self.deleted is None

  def cancel(self, isodate=None):
      if isodate is None and self.order and self.ordered:
          self.order['canceled'] = isonow()
          self.archive_order(-100)
      if isodate and self.orders:
          self.orders = [
              {**b, 'status': -100, 'canceled': isonow()}
              if b['date'] == isodate and -100 < b.get('status', 800) < 200
              else b
              for b in self.orders
          ]
          self.save()

  def bonus_text(self):
      bonus = self.album.session.pricelist.bonus
      return bonus['text'] % {'sum': bonus['sum']}

  def bonus_success(self):
      bonus = self.album.session.pricelist.bonus
      return bonus['success'] % {'sum': bonus['sum']}

  def archive_order(self, status=100):
      """
          status -100 - canceled
          status 0 - saved/received
          status 100 - confirmed/can be canceled
          status 200 - scheduled/can not be canceled
          status 300 - in work
          status 400 - digital product done
          status 500 - in printing
          status 600 - shipped
          status 700 - payed
          no status, 800 - finished, archived
      """
      if not self.order:
          return
      if 'date' not in self.order and self.ordered:
          self.order['date'] = self.ordered.replace(microsecond=0).isoformat()
      if status is not None:
          self.order['status'] = status
      self.orders.append(self.order)
      self.order = {}
      self.ordered = None
      self.save()

  def last_order_status(self, status=None):
      if status is None and self.orders:
          return self.orders[-1].get('status')
      if self.orders:
          self.orders[-1]['status'] = status
          self.save()

  def cost(self, isodate=None):
      order = None
      if isodate:
          order = next((i for i in self.orders if i['date'] == isodate), None)

      else:
          order = self.order

      if order is None:
          return 0

      price = {
          f['key']: f['price']
          for f in self.album.session.pricelist.formats
      }

      return sum(int(q) * price[k.split('_')[-1]] for k, q in self.order.items() if '_' in k)

  def status_ru(self, status):
      return {
          -100: 'Отменен',
          0: '',
          100: 'Принят',
          200: 'Обрабатывается',
          300: 'Обрабатывается',
          400: '',
          500: '',
          600: '',
          700: '',
          800: 'Выполнен',
          None: 'Выполнен',
      }[status]

  def orders_json(self):
      price = {
          f['key']: f['price']
          for f in self.album.session.pricelist.formats
      }

      return [
          {
              'isodate': o['date'],
              'date': datetime.fromisoformat(o['date']),
              'status_ru': self.status_ru(o.get('status')),
              'status': o.get('status'),
              'sum': sum(int(q) * price[k.split('_')[-1]] for k,q in o.items() if '_' in k)
          }
          for o in self.orders
      ]




