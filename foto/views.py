import os
import json
from uuid import uuid4
from operator import itemgetter
import pickle, json
import shutil

from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings

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

ru = str.maketrans('abcdefghijklmnopqrstuvwxyz', 'абцдефгхижклмнопэрстувшхуз')

en = str.maketrans('абцдефгхижклмнопэрстувшхуз', 'abcdefghijklmnopqrstuvwxyz')


def signed_view(request, sh, year, group, code):
  ''' sign LIKE `158_1И_8810:2X-8h6e7DcsINNwlnWRLTpsr05abY9pgsTkPwwZHhh8`
      '158_1А:vKw6vyj3opqhm46qsrvYgsHhrIpahSiTioqP-40YySw'
      '158_1И:QWhCPQxnhyvBI0ezGKg43SbU_ozaQWua4DSo_GVg_uc'
  '''
  print('sh',sh, 'year',year, 'group',group,'code',code)
  sign = f'{sh}_{year}{group}:{code}'

  try:
    unsigned = Signer().unsign(sign)

  except BadSignature:
    return HttpResponse('Код неверный')

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

  return zakaz(request, sh, cls, uuid)


def read_order(pathlib_file, format='json'):
  if format in ('pkl', 'pickle'):
    with pathlib_file.open('rb') as f:
      return pickle.load(f)

  elif format == 'json':
    with pathlib_file.open('r', encoding='utf8') as f:
      return json.load(f)

  raise ValueError('format must be json|pkl|pickle')


def save_order(pathlib_file, obj, format='json'):
  if format in ('pkl', 'pickle'):
    with pathlib_file.open('wb') as f:
      return pickle.dump(obj, f)

  elif format == 'json':
    with pathlib_file.open('w', encoding='utf8') as f:
      return json.dump(obj, f, ensure_ascii=False)

  raise ValueError('format must be json|pkl|pickle')


def zakaz(request, sh=None, cls=None, uuid=None):
  '''uuid like 7f094d61-bb45-4375-81fe-32fcbb383d5c'''

  if sh is None:
    return render(request, 'zakaz_index.html', {
      'schools': sorted([ {"name":i.name,"title":f"Школа {i.name}"} for i in (settings.MEDIA_ROOT / 'blanks').iterdir()], key=itemgetter('name')),
    })

  if cls is None:
    return render(request, 'zakaz_index.html', {
      's': sh,
      'classes': sorted([ i.name for i in (settings.MEDIA_ROOT / 'blanks' / sh).iterdir()], key=lambda i: int(i[:-1])*1000+ord(i[-1].upper())),
    })

  if uuid is None:
    blanks = [{
      'uuid': i.name,
      'blk': next(i.iterdir()).name
    } for i in (settings.MEDIA_ROOT / 'blanks' / sh / cls).iterdir()]

    print('[s]', sh)
    print('[c]', cls)
    print('[blanks]', blanks)

    return render(request, 'zakaz_index.html', {
      "s": sh,
      "c": cls,
      'blanks': blanks,
    })

  try:
    imgname = next((settings.MEDIA_ROOT / 'blanks' / sh.upper() / cls.upper() / str(uuid)).glob('*.jpg')).name
  except StopIteration:
    return HttpResponse('Not Found', 404)

  data = request.POST

  '''goods = {
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
  }'''

  # 2023-2024
  goods = {
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

  order_format = 'json'

  order_file = settings.MEDIA_ROOT / 'orders' / f'{imgname.split(".")[0]}.{order_format}'

  if not data and order_file.is_file():
    data = read_order(order_file, format=order_format)

  if data:
    for good_name, amounts in goods.items():
      for name, item in amounts['amounts'].items():
        item["q"] = data.get(f'{good_name}_{name}', 0)

  contacts = ContactInfoForm(data or None)
  if request.method == 'POST':
    if contacts.is_valid():

      order = {k:v for k,v in data.items() if k != 'csrfmiddlewaretoken' and v != '0'}
      print('[imgname]', imgname)  # 158_1И_8810.jpg
      print('[order]', order)  # {'vint_tshirt': '1', 'tel': 'test', 'mail': 'test@test.ru', 'name': 'test'}

      # TODO save order
      save_order(order_file, order, format=order_format)

      return render(request, 'zakaz_index.html', {'message': 'Спасибо за заказ!'})

    else:
      # import ipdb;ipdb.set_trace()
      print('NOT VALID ContactInfoForm')

  return render(request, 'zakaz.html', {
    "goods": goods,
    "blank": f"/media/blanks/{sh.upper()}/{cls.upper()}/{uuid}/{imgname}",
    "contacts": contacts,
    "prices": PRICES,
  })


def manage_blanks(request):
  return upload_blanks(request, edit=True)


def orders(request):
  ...


def upload_blanks(request, edit=False):
  form = UploadBlanksForm()

  if request.method == 'POST':
    action = request.POST.get('action')

    if action == 'delete':
      sh, cls = request.POST.get('link').split(':')[0].split('_')
      trg = BLANKS / sh / cls
      if trg.is_dir():
        shutil.rmtree(trg)

    elif action == 'upload':
      form = UploadBlanksForm(request.POST, request.FILES)
      if form.is_valid():
        sh = form.cleaned_data['sh'].upper()
        yr = form.cleaned_data["yr"]
        gr = form.cleaned_data["gr"][0].lower()
        gr = gr.translate(ru).upper()

        cls_dir = BLANKS / sh / f'{yr}{gr}'
        cls_dir.mkdir(parents=True, exist_ok=True)

        existing_file_dirs = {}
        for file_dir in cls_dir.iterdir():
          for f in file_dir.iterdir():
            img = f.name.split('.')[0].split('_')[-1]
            existing_file_dirs[img] = [file_dir, f]

        for file in request.FILES.getlist('files'):
          img, ext = file.name.split('.')
          img = img.split('_')[-1]
          exist_file_dir, exist_trg_file = existing_file_dirs.get(img) or [None, None]
          if exist_file_dir:
            file_dir = exist_file_dir
          else:
            file_dir = cls_dir / str(uuid4())
            file_dir.mkdir()
          trg_file = file_dir / f'{sh}_{yr}{gr}_{img}.{ext}'
          if trg_file.exists():
            trg_file.unlink()
          with trg_file.open('wb') as f:
            for ch in file.chunks():
              f.write(ch)

  links = []
  signer = Signer()
  for sh in BLANKS.iterdir():
    if not sh.is_dir():continue
    for cls in sh.iterdir():
      if not cls.is_dir():continue
      links.append([
        signer.sign(f'{sh.name}_{cls.name}'),
        len([None for i in cls.iterdir() if i.is_dir()]),
        sh.name,
        cls.name,
      ])

  links.sort(key=lambda i: i[0])

  return render(request, 'upload_blanks.html', {
    'form': form,
    'links': links,
    'edit': edit,
  })


def money_table(request, sh, year, group, code):

  sign = f'{sh}_{year}{group}:{code}'
  cls = f'{year}{group.upper()}'

  try:
    unsigned = Signer().unsign(sign)

  except BadSignature:
    return HttpResponse('Код неверный')

  table = []
  total = {'name': 'ВСЕГО', 'sum': 0, 'img':''}

  for file in ORDERS.iterdir():
    if not file.name.endswith('.json'):continue
    if not file.name.startswith(f'{sh}_{year}{group}_'):continue
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

  content = []

  for file in ORDERS.iterdir():
    if not file.is_file() or not file.name.endswith('.json'):continue
    if not file.name.startswith(sh_cls):continue
    img = file.name.split('.')[0].split('_')[-1]
    data = read_order(file)
    content.append([
      file.name,
      img,
      data['name'],
      f'{data["tel"]},{data["mail"]}',
    ] + to_csv_order(data))

  content = '\n'.join(';'.join(row) for row in content)
  sh_cls = sh_cls.lower().translate(en)
  filename = f"{sh_cls}_web.csv"
  response = HttpResponse(content, content_type='application/text charset=utf-8')
  response['Content-Disposition'] = f'attachment; filename="{filename}"'.encode()

  return response

