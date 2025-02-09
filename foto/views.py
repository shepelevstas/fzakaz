from datetime import datetime, timedelta
from uuid import uuid4
from operator import itemgetter
import shutil
import json
from copy import deepcopy

from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings

from utils import log
from utils.io import write_table, read_table, save_order, read_order
from utils.trans import en, ru
from utils.money import order_cost

from .forms import ContactInfoForm, UploadBlanksForm


BLANKS = settings.MEDIA_ROOT / 'blanks'
ORDERS = settings.MEDIA_ROOT / 'orders'

PRICES_23_24 = {
  "f10":     350,
  "f15":     350,
  "f20":     400,
  "f30":     500,
  "m10":     350,
  "m15":     400,
  "calend":  500,
  "rasp":    500,
  "pill":   1000,
  "mug":     700,
  "tshirt": 1000,
  "tsize":     0,
  "book":   1300,
  "set":    1000,
}

PRICES = PRICES_23_24

COL_NAME = (
  ("all", "Все фото"),
  ("port", "Портрет"),
  ("vint", "Виньетка"),
  ("coll", "Коллаж"),
)

ROW_NAME = (
  ("set", "Выгодный комплект (портрет, коллаж и виньетка 20х30)"),
  ("book", "Фотокнига (обложка - коллаж, разворот - виньетка)"),
  ("f10",    "Фото 10х15"),
  ("f15",    "Фото 15х23"),
  ("f20",    "Фото 20х30"),
  ("f30",    "Фото 30х42"),
  ("m10",    "Магнит 10х15"),
  ("m15",    "Магнит 15х23"),
  ("calend", "Календарь 30x42"),
  ("rasp",   "Расписание 30x42"),
  ("pill",   "Подушка"),
  ("mug",    "Кружка"),
  ("tshirt", "Футболка"),
  ("tsize",  "Обхват груди"),
)

NAMES = []

for k,v in COL_NAME:
  for kk,vv in ROW_NAME:
    NAMES.append((f'{k}_{kk}', f'{v} {vv}'))

COLS = [
  'all',
  'port',
  'vint',
  'coll',
]

ROWS = [
  None,
  "f15",  # 1
  "f20",
  "f30",
  "m10",
  "m15",
  "calend",
  "rasp",
  "pill",
  "mug",
  "tshirt",  # 10
  "book",
  "set",
  "eport",
  "f10",
]

signer = Signer()


def signed_view(request, session, sh, year, group, code):
  ''' sign LIKE `158_1И_8810:2X-8h6e7DcsINNwlnWRLTpsr05abY9pgsTkPwwZHhh8`
      '158_1А:vKw6vyj3opqhm46qsrvYgsHhrIpahSiTioqP-40YySw'
      '158_1И:QWhCPQxnhyvBI0ezGKg43SbU_ozaQWua4DSo_GVg_uc'
  '''
  year = str(year)
  print('sh',sh, 'year',year, 'group',group,'code',code)
  sign = f'{session}__{sh}_{year}{group}:{code}'

  try:
    unsigned = Signer().unsign(sign)
    print('[unsigned]', unsigned)

  except BadSignature:
    return HttpResponse('Код неверный')

  return zakaz(request, session, sh, year, group)

  album = Album(session, sh, year, group, None, None)



  sh, *cls_img = unsigned.split('_')
  cls = cls_img[0]

  cls_dir = BLANKS/sh.upper()/cls.upper()

  img = uuid = None
  if len(cls_img) == 2:
    img = cls_img[1]

  if img:
    try:
      uuid = next(d.name for d in cls_dir.iterdir() if list(d.glob(f'*{img}*.jpg')))

    except StopIteration:
      return HttpResponse('Такого бланка нет', 404)

  print('[zakaz]', sh, cls, uuid)

  return zakaz(request, session, sh, year, group, uuid)

price_2023_fall = {
    "port": {
      "title": "Портрет",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 350,  "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 350,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 400,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 500,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 350,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 400,  "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 500,  "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 500,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1000, "q":0},
        "mug":    {"title": "Кружка",           "price": 700,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1000, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "style": "aspect-ratio:726/527;background-position:6.3% 3.2%;background-size:166%;transform:rotate(90deg);margin:13.7% 0;border-radius:0;",
    },

    "vint": {
      "title": "Виньетка",
      "amounts": {
        "f15":    {"title": "Фото 15х23",       "price": 350,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 400,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 500,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 350,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 400,  "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 500,  "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 500,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1000, "q":0},
        "mug":    {"title": "Кружка",           "price": 700,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1000, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "style": "aspect-ratio:726/527;background-size:166%;background-position:6.3% 48.5%;",
    },

    "coll": {
      "title": "Коллаж",
      "amounts": {
        "f15":    {"title": "Фото 15х23",       "price": 350, "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 400, "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 500, "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 350, "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 400, "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 500, "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 500, "q":0},
        "pill":   {"title": "Подушка",          "price": 1000, "q":0},
        "mug":    {"title": "Кружка",           "price": 700,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1000, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "style": "aspect-ratio:726/527;background-size:166%;background-position:6.3% 94%;",
    },

    "all": {
      "title": "Все фото",
      "amounts": {
        "book": {
          "title": "Фотокнига (обложка - коллаж, разворот - виньетка)",
          "price": 1300, "q":0},
        "set":  {
          "title": "Выгодный комплект (портрет, коллаж и виньетка 20х30)",
          "price": 1000, "q":0},
      },
      "style": "aspect-ratio:1205/1795;background-size:100%;background-position:center;",
    },
  }

PRICELISTS = {
  'default': price_2023_fall,
  'price_old': {
    "port": {
      "title": "Портрет",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 300, "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 300, "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 350, "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 450, "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 300, "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 350, "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 450, "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 450, "q":0},
        "pill":   {"title": "Подушка",          "price": 850, "q":0},
        "mug":    {"title": "Кружка",           "price": 600, "q":0},
        "tshirt": {"title": "Футболка",         "price": 950, "q":0},
        "tsize":   {"title": "Обхват груди", "price": 0,   "q":0},
      },
      "style": "aspect-ratio:726/527;background-position:6.3% 3.2%;background-size:166%;transform:rotate(90deg);margin:13.7% 0;border-radius:0;",
    },

    "vint": {
      "title": "Виньетка",
      "amounts": {
        "f15":    {"title": "Фото 15х23",       "price": 300, "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 350, "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 450, "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 300, "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 350, "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 450, "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 450, "q":0},
        "pill":   {"title": "Подушка",          "price": 850, "q":0},
        "mug":    {"title": "Кружка",           "price": 600, "q":0},
        "tshirt": {"title": "Футболка",         "price": 950, "q":0},
        "tsize":   {"title": "Обхват груди", "price": 0,   "q":0},
      },
      "style": "aspect-ratio:726/527;background-size:166%;background-position:6.3% 48.5%;",
    },

    "coll": {
      "title": "Коллаж",
      "amounts": {
        "f15":    {"title": "Фото 15х23",       "price": 300, "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 350, "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 450, "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 300, "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 350, "q":0},
        "calend": {"title": "Календарь 30x42",  "price": 450, "q":0},
        "rasp":   {"title": "Расписание 30x42", "price": 450, "q":0},
        "pill":   {"title": "Подушка",          "price": 850, "q":0},
        "mug":    {"title": "Кружка",           "price": 600, "q":0},
        "tshirt": {"title": "Футболка",         "price": 950, "q":0},
        "tsize":   {"title": "Обхват груди", "price": 0,   "q":0},
      },
      "style": "aspect-ratio:726/527;background-size:166%;background-position:6.3% 94%;",
    },

    "all": {
      "title": "Все фото",
      "amounts": {
        "book": {"title": "Фотокнига (обложка - коллаж, разворот - виньетка)",         "price": 990, "q":0},
        "set":  {"title": "Выгодный комплект (портрет, коллаж и виньетка 20х30)", "price": 800, "q":0},
      },
      "style": "aspect-ratio:1205/1795;background-size:100%;background-position:center;",
    },
  },
  'price_2023_fall': price_2023_fall,
  'price_2025_spring': {
    "8mar": {
      "title": "8 Марта",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 400,  "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 450,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 500,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 600,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 500,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 600,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1200, "q":0},
        "mug":    {"title": "Кружка",           "price": 800,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1200, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "blank_img_style": "aspect-ratio:8/12;background-size:201%;",
    },
    "23feb": {
      "title": "23 Февраля",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 400,  "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 450,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 500,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 600,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 500,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 600,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1200, "q":0},
        "mug":    {"title": "Кружка",           "price": 800,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1200, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "blank_img_style": "aspect-ratio:8/12;background-size:200%;background-position:100% 100%;transform: rotate(-90deg) scale(.6666);margin: -43% 0;",
    },
    "9may": {
      "title": "9 Мая",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 400,  "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 450,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 500,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 600,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 500,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 600,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1200, "q":0},
        "mug":    {"title": "Кружка",           "price": 800,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1200, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "blank_img_style": "aspect-ratio:8/12;background-size:200%;background-position:0% 100%;transform: rotate(-90deg) scale(.6666);margin: -43% 0;",
    },
    "pozdr": {
      "title": "Поздравляю!",
      "amounts": {
        "f10":    {"title": "Фото 10х15",       "price": 400,  "q":0},
        "f15":    {"title": "Фото 15х23",       "price": 450,  "q":0},
        "f20":    {"title": "Фото 20х30",       "price": 500,  "q":0},
        "f30":    {"title": "Фото 30х42",       "price": 600,  "q":0},
        "m10":    {"title": "Магнит 10х15",     "price": 500,  "q":0},
        "m15":    {"title": "Магнит 15х23",     "price": 600,  "q":0},
        "pill":   {"title": "Подушка",          "price": 1200, "q":0},
        "mug":    {"title": "Кружка",           "price": 800,  "q":0},
        "tshirt": {"title": "Футболка",         "price": 1200, "q":0},
        "tsize":  {"title": "Обхват груди",     "price": 0,    "q":0},
      },
      "blank_img_style": "aspect-ratio:8/12;background-size:200%;background-position:100% 0%;transform: rotate(-90deg) scale(.6666);margin: -43% 0;",
    },
    "BONUS": {
      "text": "При заказе от 2000р - все четыре электронные фото - в подарок!",
      "success": "Все четыре электронные фото - в подарок!",
      "sum": 2000,
    },
  },
}

class Album:
  from functools import lru_cache

  def __init__(self, session, sh, shyear, group, uuid=None, imgn=None):
    self.session = session
    self.sh = sh
    self.shyear = shyear
    self.group = group
    self.cls = group
    self.uuid = uuid
    self.imgn = imgn
    self.blanks_top = settings.MEDIA_ROOT / 'blanks'
    self.blanks_ses = self.blanks_top / session
    self.blanks_sh = self.blanks_ses / sh.upper()
    self.blanks_cls = self.blanks_sh / f'{shyear.upper()}{group.upper()}'
    self.blanks_dir = self.blanks_cls
    self.order_format = 'json'
    self.orders_dir = settings.MEDIA_ROOT / 'orders'

  @property
  def is_closed(self):
    return (self.blanks_cls / 'closed').is_file()

  @property
  def blanks(self):
    style = ""
    goods = self.get_empty_goods()
    for gname, part in goods.items():
      if gname == 'BONUS': continue
      if 'blank_img_style' in part:
        style = part['blank_img_style']
        break

    return [{
      'uuid': i.name,
      'blk': next(i.iterdir()).name,
      'style': style,
    } for i in self.blanks_dir.iterdir() if i.is_dir()]

  @lru_cache
  def get_blank_file(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid
    return next((self.blanks_dir / str(uuid)).glob('*.jpg'))

  def get_imgname(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_imgname'
    return self.get_blank_file(uuid).name
    # return next((self.blanks_dir / str(uuid)).glob('*.jpg')).name

  def get_img(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_img'
    filename = self.get_imgname(uuid)
    return filename.rsplit('.', 1)[0].rsplit('_', 1)[-1]

  @lru_cache
  def get_order_file(self, uuid=None, skip_check=False):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_order_file'

    f = self.get_order_file2(uuid, skip_check)

    if skip_check:
      return f

    if not f.is_file():
      f = self.orders_dir / f'{self.session}__{self.get_imgname(uuid).split(".")[0]}.{self.order_format}'

    return f.is_file() and f or None

  @lru_cache
  def get_order_file2(self, uuid=None, skip_check=False):
    uuid = uuid or self.uuid
    assert uuid
    return self.orders_dir / self.session / self.sh / f'{self.shyear}{self.group}' / (self.get_blank_file(uuid).stem + '.json')

  def save_order(self, order, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.save_order'
    f = self.get_order_file(uuid, True)
    if not f.parent.is_dir():
      f.parent.mkdir(parents=True, exist_ok=True)
    save_order(f, order, self.order_format)

  @lru_cache
  def get_order(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_order'
    order_file = self.get_order_file(uuid)
    if not order_file:
      return None
    return read_order(order_file, format=self.order_format)

  @lru_cache
  def get_pricename(self, uuid=None):
    for lvl, i in [
      ('cls', self.blanks_cls),
      ('sh', self.blanks_sh),
      ('ses', self.blanks_ses),
      ('top', self.blanks_top),
    ]:
      f = i / 'price'
      if f.is_file():
        return f.read_text().strip()

    return 'default'

  # TODO
  def get_pricefile(self, uuid=None):
    trg = None
    if uuid:
      trg = self.blanks_dir / str(uuid) / 'price.json'
    if not trg or not trg.is_file():
      trg = self.blanks_dir / 'price.json'
    if not trg.is_file():
      trg = self.blanks_sh / 'price.json'
    if not trg.is_file():
      trg = self.blanks_top / 'price.json'
    if not trg.is_file():
      return None

  def get_empty_goods(self, uuid=None):
    uuid = uuid or self.uuid
    # assert uuid, 'no uuid in album.get_empty_goods'
    pricename = self.get_pricename(uuid)
    return deepcopy(PRICELISTS.get(pricename))

  @lru_cache
  def get_goods(self, uuid=None, post_data=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_goods'
    goods = self.get_empty_goods(uuid)
    data = self.get_order(uuid)

    if data:
      for good_name, amounts in goods.items():
        if good_name == 'BONUS': continue
        for name, item in amounts['amounts'].items():
          item["q"] = data.get(f'{good_name}_{name}', 0)

    if post_data:
      for good_name, part in goods.items():
        if good_name == 'BONUS': continue
        for line_name, item in part['amounts'].items():
          k = f'{good_name}_{line_name}'
          v = next((j for i,j in post_data if i == k), None)
          if v is not None:
            item['q'] = v

    return goods

  def get_blank_url(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_blank_url'
    return f"/media/blanks/{self.session}/{self.sh.upper()}/{self.shyear}{self.group}/{uuid}/{self.get_imgname(uuid)}"

  @classmethod
  def get_albums(cls, ses=None, sh=None):
    res = []
    for SES in BLANKS.iterdir():
      if not SES.is_dir(): continue
      if ses and SES.name != ses: continue
      for SH in SES.iterdir():
        if not SH.is_dir(): continue
        if sh and SH.name != sh: continue
        for ALB in SH.iterdir():
          if not ALB.is_dir(): continue
          res.append(Album(SES.name, SH.name, ALB.name[:-1], ALB.name[-1:], None, None))

    res.sort(key=lambda a: (a.session, a.sh, int(a.shyear), a.group.upper()))

    return res

  @property
  @lru_cache
  def ordered_count(self):
    return sum([
      self.get_order_file(uudir.name) is not None
      for uudir in self.blanks_dir.iterdir() if uudir.is_dir()
    ])

  @property
  @lru_cache
  def blanks_count(self):
    return sum([uudir.is_dir() for uudir in self.blanks_dir.iterdir()])

  @classmethod
  def order_cost(cls, path):
    # TODO:
    return 1000

  @property
  def order_progress(self):
    return self.ordered_count / self.blanks_count * 100

  @property
  def name(self):
    return f'{self.sh}_{self.shyear}{self.group}'

  @property
  def id(self):
    return f'{self.session}__{self.name}'

  @property
  def sign(self):
    return signer.sign(self.id)

  def get_json(self):
    return {
      'id': self.id,
      'name': self.name,
      'sh': self.sh,
      'cls': f'{self.shyear}{self.group}',
      'sign': self.sign,
      'signed_url': self.signed_url,
      'blanks_count': self.blanks_count,
      'ordered_count': self.ordered_count,
      'order_progress': self.order_progress,
      'closed': self.is_closed,
      'is_closed': self.is_closed,
    }

  @property
  def signed_url(self):
    return self.sign

  @property
  def money_table_url(self):
    sign = signer.sign(self.id)
    adr, code = sign.split(':')
    return f'{code}/{adr}/money_table/'

  @lru_cache
  def get_money_table(self):
    blanks = {
      next(uudir.glob('*.jpg')).stem: self.get_order(uudir.name)
      for uudir in self.blanks_dir.iterdir() if uudir.is_dir()
    }

    pricelist = self.get_empty_goods()

    cols = {}
    rows = {}
    total = 0

    for img, b in blanks.items():
      if b is None: continue
      for item, q in b.items():
        if '_' not in item: continue
        col_k, row_k = item.split('_')
        if row_k == 'tsize': continue
        if col_k not in pricelist: continue
        col_data = pricelist[col_k]
        if row_k not in col_data['amounts']: continue
        row_data = col_data['amounts'][row_k]
        price = row_data["price"]
        col = cols.setdefault(item, {'q': 0, 'title': f'{row_data["title"]} "{col_data["title"]}" ({price}₽)'})
        q = int(q)
        col['q'] += q
        row = rows.setdefault(img, {'total': 0, 'title': img})
        row[item] = q
        row['total'] += q * price
        total += q * price

    cols = dict(sorted((i for i in cols.items()), key=lambda i:i[1]['title']))
    rows = dict(sorted((i for i in rows.items()), key=lambda i:i[0]))

    return {
      'cols': cols,
      'rows': rows,
      'total': total,
    }

  def cancel_order(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'not uuid in album.cancel_order'
    # delete order.json
    order_file = self.get_order_file(uuid)
    if order_file.is_file():
      order_file.unlink()
      return
    return 'Not a file'


def zakaz(request, session=None, sh=None, shyear=None, group=None, uuid=None, imgn=None):
  '''uuid like 7f094d61-bb45-4375-81fe-32fcbb383d5c'''

  shyear = str(shyear)

  if sh is None:
    return render(request, 'zakaz_index.html', {
      'schools': sorted([ {"name":i.name,"title":f"Школа {i.name}"} for i in (settings.MEDIA_ROOT / 'blanks').iterdir()], key=itemgetter('name')),
    })

  if shyear is None or group is None:
    return render(request, 'zakaz_index.html', {
      's': sh,
      'classes': sorted([ i.name for i in (settings.MEDIA_ROOT / 'blanks' / sh).iterdir()], key=lambda i: int(i[:-1])*1000+ord(i[-1].upper())),
    })

  album = Album(session, sh, shyear, group, uuid, imgn)

  if uuid is None:

    return render(request, 'zakaz_index.html', {
      "ses": session,
      'session':session,
      "sh": sh,
      "shyear": shyear,
      'year': shyear,
      "group": group,
      "cls": f'{shyear}{group}',
      # "c": cls,
      # 'blanks': blanks,
      'blanks': album.blanks,
      'album': album,
    })

  # ZAKAZ

  contacts = ContactInfoForm(request.POST or album.get_order() or None)

  order = None

  if request.method == 'POST':
    order = dict(i for i in request.POST.items() if i[0] not in ['csrfmiddlewaretoken', 'action'] and i[1] != '0')

    if contacts.is_valid():

      action = request.POST.get('action')
      message = ''

      if action == 'save':
        album.save_order(order)
        message = 'Спасибо за заказ!'

      elif action == 'cancel_order':
        album.cancel_order()
        message = 'Заказ отменен!'

      return render(
        request, 'zakaz_index.html',
        {'message': message},
      )

    else:
      # import ipdb;ipdb.set_trace()
      print('NOT VALID ContactInfoForm')
      print(contacts.errors)

  return render(request, 'zakaz.html', {
    "goods": album.get_goods(post_data=tuple(order.items()) if order else None),
    "blank": album.get_blank_url(),
    "contacts": contacts,
    "album": album,
  })


def manage_blanks(request):
  return upload_blanks(request, edit=True)


def orders(request):
  ...


def load_album(ALBUM):
  album = f'{ALBUM.parent.name}_{ALBUM.name}'
  blanks_count = len([None for i in ALBUM.iterdir() if i.is_dir()])
  closed = (ALBUM / 'closed').is_file()
  ordered_count = 0
  for o in ORDERS.iterdir():
    if not o.name.startswith(f'{album}_'): continue
    order = read_order(o)
    if order_cost(order):
      ordered_count += 1
  return {
    'name': album,
    'sh': ALBUM.parent.name,
    'cls': ALBUM.name,
    'sign': signer.sign(album),
    'blanks_count': blanks_count,
    'ordered_count': ordered_count,
    'order_progress': ordered_count / blanks_count * 100,
    'closed': closed,
  }


def upload(request):
  form = UploadBlanksForm(request.POST, request.FILES)
  if form.is_valid():
    ses = form.cleaned_data['session']
    sh = form.cleaned_data['sh'].upper()
    yr = form.cleaned_data["yr"]
    gr = form.cleaned_data["gr"][0].lower().translate(ru).upper()

    ALBUM = BLANKS / ses / sh / f'{yr}{gr}'
    ALBUM.mkdir(parents=True, exist_ok=True)

    existing_file_dirs = {}
    for file_dir in ALBUM.iterdir():
      if not file_dir.is_dir():continue
      for f in file_dir.iterdir():
        img = f.name.rsplit('.',1)[0]
        existing_file_dirs[img] = [file_dir, f]

    for file in request.FILES.getlist('files'):
      img, ext = file.name.rsplit('.', 1)
      exist_file_dir, exist_trg_file = existing_file_dirs.get(img) or [None, None]
      if exist_file_dir:
        file_dir = exist_file_dir
      else:
        file_dir = ALBUM / str(uuid4())
        file_dir.mkdir()
      trg_file = file_dir / f'{img}.{ext}'
      if trg_file.exists():
        trg_file.unlink()
      with trg_file.open('wb') as f:
        for ch in file.chunks():
          f.write(ch)

  if request.POST.get('ajax') == 'true':
    # album_data = load_album(ALBUM)
    album = Album(ses, sh, yr, gr, None, None)
    return JsonResponse({'data': album.get_json()})


def upload_blanks(request, edit=False):
  form = UploadBlanksForm()

  if request.method == 'POST':
    log('[ upload_blanks POST ]', request.POST)
    action = request.POST.get('action')
    session = sh = cls = ALBUM = None

    if 'link' in request.POST:
      sh, cls = request.POST['link'].split(':')[0].split('_')
      ALBUM = BLANKS / sh / cls

    if action == 'delete':
      trg = ALBUM
      if trg.is_dir():
        shutil.rmtree(trg)

    elif action == 'upload':
      res = upload(request)
      if res:
        return res

    elif action == 'close':
      log('[ CLOSE ]')
      closed = ALBUM / 'closed'
      closed.open('a').close()

    elif action == 'open':
      log('[ OPEN ]', ALBUM, ALBUM.is_dir())
      closed = ALBUM / 'closed'
      log('is file', closed.is_file())
      if closed.is_file():
        closed.unlink()

  ses = request.GET.get('ses')
  sh = request.GET.get('sh')

  return render(request, 'manage_blanks.html', {
    'form': form,
    'edit': edit,
    'albums': Album.get_albums(ses, sh),
  })


def money_table2(req, session, sh, shyear, group, code):
  shyear = str(shyear)
  sign = f'{session}__{sh}_{shyear}{group}'
  try:
    assert sign == signer.unsign(f'{sign}:{code}')
  except (BadSignature, AssertionError):
    return HttpResponse('Страница не найдена')

  album = Album(session, sh, shyear, group)

  return render(req, 'money_table2.html', {'album':album})


def money_table(request, session, sh, shyear, group, code):

  sign = f'{sh}_{year}{group}:{code}'
  cls = f'{year}{group.upper()}'

  try:
    unsigned = signer.unsign(sign)

  except BadSignature:
    return HttpResponse('Код неверный')

  after = None
  if request.GET.get('after'):
    y,m,d = map(int, request.GET['after'].split('-')[:3])
    after = datetime.now().replace(year=y, month=m, day=d, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

  table = []
  total = {'name': 'ВСЕГО', 'sum': 0, 'img':''}

  for file in ORDERS.iterdir():
    if not file.name.endswith('.json'):continue
    if not file.name.startswith(f'{sh}_{year}{group}_'):continue
    if after and after > datetime.fromtimestamp(file.stat().st_mtime):continue
    data = read_order(file)
    img = file.name.split('.')[0].split('_')[-1]
    data['img'] = img
    data['sum'] = 0
    img_sum = 0
    table.append(data)
    for k,v in data.items():
      if not v or not isinstance(v, (int, str)):continue
      if '_' not in k:continue
      col, row = k.split('_')
      price = PRICES.get(row, 0)
      if row in ('tsize',):continue
      if col in ('port', 'vint', 'coll', 'all'):
        img_sum += price * int(v)
        total[k] = total.get(k, 0) + int(v)
    data['sum'] = img_sum
    total['sum'] += img_sum

  total['img'] = len(table)

  for SH in BLANKS.iterdir():
    if not SH.is_dir() or SH.name != sh:continue
    for CLS in SH.iterdir():
      if not CLS.is_dir() or CLS.name != cls:continue
      for uu in CLS.iterdir():
        if not uu.is_dir():continue
        for f in uu.iterdir():
          if not f.is_file() or not f.name.endswith('.jpg'):continue
          img = f.name.split('.')[0].split('_')[-1]
          tmp = next((i for i in table if i['img'] == img), None)
          if tmp is None:
            table.append({'img':img, 'sum':0, 'name':'', 'uuid': uu.name})
          else:
            tmp['uuid'] = uu.name

  total['img'] = f'{total["img"]} из {len(table)}'

  table.append(total)
  table.insert(0, total)

  names = [i for i in NAMES if i[0] in total]

  return render(request, 'money_table.html', {
    'sh': sh,
    'cls': cls,
    'sh_cls': f'{sh}_{cls}',
    'code': code,
    'year': year,
    'group': group,
    'table': table,
    'names': names,
  })


def to_csv_order(data):
  res = []

  for k,v in data.items():
    if v == '': continue
    if '_' not in k: continue
    col, row = k.split('_')
    if col not in COLS: continue
    if row not in ROWS: continue
    col_i = COLS.index(col)
    row_i = ROWS.index(row)
    if col == 'all':
      v = f'{row_i},1,{int(v)}'
    elif row == 'tshirt':
      v = f'{row_i},{col_i},{int(v)},{data.get(f"{col}_tsize","??")}'
    else:
      v = f'{row_i},{col_i},{int(v)}'
    res.append(v)

  return res


def download_orders(request, sh_cls, code):
  sign = f'{sh_cls}:{code}'

  try:
    unsigned = Signer().unsign(sign)

  except BadSignature:
    return HttpResponse('Код неверный')

  after = []
  if request.GET.get('after'):
    y,m,d = map(int, request.GET['after'].split('-')[:3])
    after = datetime.now().replace(year=y, month=m, day=d, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

  content = []

  for file in ORDERS.iterdir():
    if not file.is_file() or not file.name.endswith('.json'):continue
    if not file.name.startswith(sh_cls):continue
    if after and after > datetime.fromtimestamp(file.stat().st_mtime):continue
    img = file.name.split('.')[0].split('_')[-1]
    data = read_order(file)
    content.append([
      img,
      data['name'],
      f'{data["tel"]},{data["mail"]}',
    ] + to_csv_order(data))

  content = '\n'.join(';'.join(row) for row in content)
  #content = chr(1025).join(content.split(chr(203)))
  content = content.replace(chr(203), 'Ё')
  content = content.replace(chr(235), 'ё')
  content = content.encode('cp1251')
  sh_cls = sh_cls.lower().translate(en)
  filename = f"{sh_cls}_web.csv"
  response = HttpResponse(content, content_type='application/text charset=utf-8')
  response['Content-Disposition'] = f'attachment; filename="{filename}"'.encode()

  return response


def play(req):
  log('[ POST ]', req.POST)
  form = ContactInfoForm(req.POST or None)
  log('[ is_valid ]', form.is_valid())
  if hasattr(form, 'cleaned_data'):
    log('[ cleaned_data ]', form.cleaned_data)
  if not form.is_valid():
    log('[ errors ]', form.errors)

  return render(req, 'play.html', {'form': form})

