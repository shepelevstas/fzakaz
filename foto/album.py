import shutil
from functools import lru_cache
from copy import deepcopy

from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.utils import timezone as tz

from utils.io import save_order, read_order



signer = Signer()



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

    "BONUS": {
      "text": "При заказе от 2000р - все четыре электронные фото - в подарок!",
      "success": "Все четыре электронные фото - в подарок!",
      "sum": 2000,
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

  def __init__(self, session, sh, shyear, group, uuid=None, imgn=None):
    shyear = str(shyear)
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

  def __str__(self):
    return f'Album(<{self.session}__{self.sh}_{self.shyear}{self.group}>)'

  @classmethod
  def from_sign(cls, sign):
    ses__sh_yrgr = None
    try:
      ses__sh_yrgr = signer.unsign(sign)
    except:
      return
    ses, sh_yrgr = ses__sh_yrgr.split('__', 1)
    sh, yrgr = sh_yrgr.split('_', 1)
    yr = yrgr[:-1]
    gr = yrgr[-1]
    return cls(ses, sh, yr, gr)

  @property
  @lru_cache
  def is_closed(self):
    return (self.blanks_cls / 'closed').is_file() or self.is_deleted

  def close(self):
    return (self.blanks_cls / 'closed').open('a').close()

  def unclose(self):
    close_file = self.blanks_cls / 'closed'
    return close_file.unlink() if close_file.is_file() else None

  def delete(self, forreal=False):
    if forreal:
      return shutil.rmtree(self.blanks_cls)
    return (self.blanks_cls / 'deleted').open('a').close()

  def undelete(self):
    file = self.blanks_cls / 'deleted'
    if file.is_file():
      return file.unlink()

  @property
  @lru_cache
  def is_deleted(self):
    return (self.blanks_cls / 'deleted').is_file()

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
    return self.get_blank_file(uuid).stem

  def get_img(self, uuid=None):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_img'
    imgname = self.get_imgname(uuid)
    return imgname.rsplit('_', 1)[-1]

  @lru_cache
  def get_order_file(self, uuid=None, skip_check=False):
    uuid = uuid or self.uuid
    assert uuid, 'no uuid in album.get_order_file'

    f = self.get_order_file2(uuid, skip_check)

    if skip_check:
      return f

    if not f.is_file():
      f = self.orders_dir / f'{self.session}__{self.get_imgname(uuid)}.{self.order_format}'

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
    zone = tz.zoneinfo.ZoneInfo('Asia/Krasnoyarsk')
    data = tz.now().replace(microsecond=0).astimezone(zone).isoformat()
    order['date'] = date
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
    return f"/media/blanks/{self.session}/{self.sh.upper()}/{self.shyear}{self.group}/{uuid}/{self.get_blank_file(uuid).name}"

  @classmethod
  def get_albums(cls, ses=None, sh=None):
    res = []
    for SES in (settings.MEDIA_ROOT / 'blanks').iterdir():
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

  # TODO:
  @classmethod
  def order_cost(cls, path):
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
      (next(uudir.glob('*.jpg')).stem, uudir.name): self.get_order(uudir.name)
      for uudir in self.blanks_dir.iterdir() if uudir.is_dir()
    }

    pricelist = self.get_empty_goods()

    cols = {}
    rows = {}
    total = 0

    for (img, uuid), b in blanks.items():
      if b is None: continue
      row = {
        'contact': {'tel': b['tel'], 'mail': b['mail'], 'name': b['name']},
        'total': 0,
        'img': img,
        'title': img,
        'uuid': uuid,
        'items': {},
        'date': b.get('date') or '',
      }
      rows[img] = row

      for item, q in b.items():
        if '_' not in item: continue
        col_k, row_k = item.split('_')
        if row_k == 'tsize':
          row['tsize'] = q
          continue
        if col_k not in pricelist: continue
        col_data = pricelist[col_k]
        if row_k not in col_data['amounts']: continue
        row_data = col_data['amounts'][row_k]
        price = row_data["price"]
        col = cols.setdefault(item, {
          'q': 0,
          'theme_k': col_k,
          'theme': col_data['title'],
          'format_k': row_k,
          'format': row_data['title'],
          'price': price,
        })
        q = int(q)
        col['q'] += q
        row['items'][item] = q
        row['total'] += q * price
        total += q * price

    cols = dict(sorted(cols.items(), key=lambda i:(i[1]['format'],i[1]['theme'])))
    rows = dict(sorted(rows.items(), key=lambda i:i[0]))

    return {
      'session': self.session,
      'sh': self.sh,
      'year': self.shyear,
      'group': self.group,
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



