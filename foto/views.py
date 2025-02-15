from datetime import datetime, timedelta
from uuid import uuid4
from operator import itemgetter
import shutil
import json

from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings

from utils import log
from utils.io import save_order, read_order
from utils.trans import en, ru
from utils.money import order_cost

from .forms import ContactInfoForm, UploadBlanksForm
from .album import Album


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
    order = dict(i for i in request.POST.items() if i[0] not in ['csrfmiddlewaretoken', 'action'] and i[1] and i[1] != '0')

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
        existing_file_dirs[f.name] = [file_dir, f]

    for file in request.FILES.getlist('files'):
      exist_file_dir, exist_trg_file = existing_file_dirs.get(file.name) or [None, None]
      if exist_file_dir:
        file_dir = exist_file_dir
      else:
        file_dir = ALBUM / str(uuid4())
        file_dir.mkdir()
      trg_file = file_dir / file.name
      if trg_file.exists():
        trg_file.unlink()
      with trg_file.open('wb') as f:
        for ch in file.chunks():
          f.write(ch)

  if request.POST.get('ajax') == 'true':
    album = Album(ses, sh, yr, gr, None, None)
    return JsonResponse({'data': album.get_json()})


def upload_blanks(request, edit=False):
  if request.method == 'POST':
    log('[ upload_blanks POST ]', request.POST)
    action = request.POST.get('action')
    album = None

    if action == 'upload':
      res = upload(request)
      if res:
        return res

    if 'album_sign' in request.POST:
      album = Album.from_sign(request.POST['album_sign'])

    log('[album]', album)
    log('[action]', action)
    log('[has action]', hasattr(album, action))

    if album and hasattr(album, action):
      getattr(album, action)()

  ses = request.GET.get('ses')
  sh = request.GET.get('sh')

  return render(request, 'manage_blanks.html', {
    'form': UploadBlanksForm(),
    'edit': edit,
    'albums': Album.get_albums(ses, sh),
  })


def money_table2(req, session, sh, shyear, group, code):
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


def orders_file(req, sign):
  album = Album.from_sign(sign)

  content = json.dumps(album.get_money_table(), ensure_ascii=False)

  res = HttpResponse(content, content_type='application/text charset=utf-8')
  res['Content-Disposition'] = f'attachment; filename="{album.id}.json"'.encode()

  return res


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
      file.name,
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

