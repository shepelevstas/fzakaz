import re
from datetime import datetime, timedelta
from uuid import uuid4
from operator import itemgetter
import json

from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
#from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings

from utils import log
from utils.io import read_order
from utils.trans import en, ru
from utils.money import order_cost

from .forms import ContactInfoForm, UploadBlanksForm
from .album import Album

from .models import Session, Order, Pricelist


signer = Signer()


def signed_view(request, sign):
  ''' sign LIKE `Spring_2025__158_1И:2X-8h6e7DcsINNwlnWRLTpsr05abY9pgsTkPwwZHhh8`
  '''
  try:
    unsigned = signer.unsign(sign)
    session, sh, year, group = re.match(r'(.+)__(.+)_(\d+)(\D)', unsigned).groups()
  except BadSignature:
    return HttpResponse('Код неверный'.encode())

  return zakaz(request, session, sh, year, group)


def blanks(req, sign):
  from .models import Album
  try:
    unsigned = signer.unsign(sign)
    ses, _, alb = unsigned.partition('__')
    ses_yr, _, ses_nm = ses.partition('_')
    sh, _, cls = alb.partition('_')
    yr = cls[:-1]
    gr = cls[-1]
    ses = Session.objects.select_related('pricelist').get(year=ses_yr, name=ses_nm)
    alb = Album.objects.prefetch_related('order_set').get(session=ses, sh=sh, shyear=yr, group=gr)
  except BadSignature:
    return HttpResponse('Код неверный'.encode())

  orders = alb.order_set.filter(deleted=None)
  style = next(iter(ses.pricelist.themes.values()))['blank_img_style']

  return render(req, 'blanks.html', {
    'album': alb,
    'orders': orders,
    'blank_img_style': style,
  })


def order(req, sign, id):
  from .models import Album

  try:
    unsigned = signer.unsign(sign)
    ses, _, alb_ord = unsigned.partition('__')
    ses_yr, _, ses_nm = ses.partition('_')
    alb, _, ord = alb_ord.partition('__')
    sh, _, cls = alb.partition('_')
    yr = cls[:-1]
    gr = cls[-1]
    order = Order.objects.select_related('album__session__pricelist').get(
      id=id,
      imgname=ord,
      album__sh=sh,
      album__shyear=yr,
      album__group=gr,
      album__session__year=ses_yr,
      album__session__name=ses_nm,
    )

  except (BadSignature, Order.DoesNotExist):
    return HttpResponse('Код неверный')

  contacts = ContactInfoForm(req.POST or order.json or None)

  return render(req, "order.html", {
    'order': order,
    "contacts": contacts,
  })





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

  contacts = ContactInfoForm(request.POST or album.get_order() or None, initial={'name': album.suggest_name()})

  order = None

  if request.method == 'POST':
    order = dict(i for i in request.POST.items() if i[0] not in ['csrfmiddlewaretoken', 'action'] and i[1] and i[1] != '0')
    album.post_data = order

    if contacts.is_valid():

      action = request.POST.get('action')
      message = ''

      if action == 'save':
        album.save_order(order)
        message = 'Спасибо за заказ! Пока прием заказов не закрыт, Вы всегда можете вернуться и изменить его! Это не создаст новый заказ, а изменит имеющийся! Если Вам полагается электронный портрет в подарок - не забудьте указать правильный адрес электронной почты. Можно вернуться назад и изменить контактные данные.'

      elif action == 'cancel_order':
        album.cancel_order()
        message = 'Заказ отменен!'

      return render(
        request, 'zakaz_index.html',
        {'message': message},
      )

    else:
      print('NOT VALID ContactInfoForm')
      print(contacts.errors)

  return render(request, 'zakaz.html', {
    # "goods": album.get_goods(post_data=tuple(order.items()) if order else None),
    "contacts": contacts,
    "album": album,
  })


def orders(request):
  ...


def load_album(ALBUM):
  album = f'{ALBUM.parent.name}_{ALBUM.name}'
  blanks_count = len([None for i in ALBUM.iterdir() if i.is_dir()])
  closed = (ALBUM / 'closed').is_file()
  ordered_count = 0
  for o in (settings.MEDIA_ROOT / 'orders').iterdir():
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
  form = UploadBlanksForm(request.POST, request.FILES, old=True)
  if form.is_valid():
    ses = form.cleaned_data['session']
    sh = form.cleaned_data['sh'].upper()
    yr = form.cleaned_data["yr"]
    gr = form.cleaned_data["gr"][0].lower().translate(ru).upper()

    ALBUM = settings.MEDIA_ROOT / 'blanks' / ses / sh / f'{yr}{gr}'
    ALBUM.mkdir(parents=True, exist_ok=True)

    existing_file_dirs = {
      f.name: f.parent
      for f in ALBUM.glob('**/*.jpg')
    }

    for file in request.FILES.getlist('files'):
      file_dir = existing_file_dirs.get(file.name) or ALBUM / str(uuid4())
      file_dir.mkdir(exist_ok=True)
      trg_file = file_dir / file.name
      if trg_file.exists():
        trg_file.unlink()
      with trg_file.open('wb') as f:
        for ch in file.chunks():
          f.write(ch)

  if request.POST.get('ajax') == 'true':
    album = Album(ses, sh, yr, gr, None, None)
    return JsonResponse({'data': album.get_json()})


def manage_albums(req, edit=True):
  from .models import Album

  if req.POST.get('action') == 'upload':
    form = UploadBlanksForm(req.POST, req.FILES)
    if form.is_valid():
      ses_yr, _, ses_name = form.cleaned_data['session'].partition('_')
      sh = form.cleaned_data["sh"].upper()
      yr = form.cleaned_data["yr"]
      gr = form.cleaned_data["gr"][0].lower().translate(ru).upper()
      ses = Session.objects.get(year=ses_yr, name=ses_name)
      alb, alb_is_new = Album.objects.get_or_create(session=ses, sh=sh, shyear=yr, group=gr)

      for file in req.FILES.getlist('file'):
        ord, ord_is_new = Order.objects.get_or_create(
          album=alb,
          imgname=file.name.rsplit('.', 1)[-2],
          defaults={
            'blank': file,
          },
        )
        if not ord_is_new:
          ord.blank = file
          ord.save()

      if req.POST.get('ajax') == 'true':
        return JsonResponse({'album': alb.get_json(), 'status': 'OK'})

    return JsonResponse({
      'status': 'FAIL',
      'msg': f'{form.errors}',
    })

  if req.method == 'GET' and req.GET.get('pricelist'):
    pricelist = Pricelist.objects.get(id=req.GET['pricelist'])
    return JsonResponse({
      'status': 'OK',
      # 'pricelist': {
      #   'name': pricelist.name,
      #   'formats': [f for k,f in pricelist.formats.items()],
      #   'themes': [{**th, 'formats': [pricelist.formats[f]['ru'] for f in th['formats']]} for k,th in pricelist.themes.items()],
      # },
      'pricelist': pricelist.as_json(),
    })

  albums = Album.objects.select_related('session')
  ses = req.GET.get('ses')
  sh = req.GET.get('sh')
  if ses:
    year, _, name = ses.partition('_')
    albums = albums.filter(session__year=year, session__name=name)
  if sh:
    albums = albums.filter(sh=sh)

  return render(req, 'manage_albums.html', {
    'albums': albums,
    'form': UploadBlanksForm(),
    'edit': edit,
    'prices': Pricelist.objects.filter(deleted=None).only('name'),
  })


def manage_blanks(request, edit=True):
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

  form = UploadBlanksForm(old=True)

  return render(request, 'manage_blanks.html', {
    'form': form,
    'edit': edit,
    'albums': Album.get_albums(ses, sh),
  })


def money_table_total(req):
  ses = req.GET.get('ses')
  sh = req.GET.get('sh')

  albums = Album.get_albums(ses, sh)

  album = {
    'name': '<name>',
    'session': ses,
    'sh': sh,
    'shyear': '2025',
    'group': '<group>',
    'ordered_count': 0,
    'blanks_count': 0,
    'get_money_table': {
      'cols': {},
      'rows': {},
      'total': 0,
    },
  }

  for a in albums:
    album['blanks_count'] += a.blanks_count
    album['ordered_count'] += a.ordered_count

    mtable = a.get_money_table()

    for item, col in mtable['cols'].items():
      c = album['get_money_table']['cols'].get(item)
      if c:
        c['q'] += col['q']
      else:
        album['get_money_table']['cols'][item] = col

    for item, row in mtable['rows'].items():
      album['get_money_table']['rows'][item] = row

  return render(req, 'money_table2.html', {
    'album': album,
  })


def money_table2(req, session, sh, shyear, group, code):
  id = f'{session}__{sh}_{shyear}{group}'
  try:
    assert id == signer.unsign(f'{id}:{code}')
  except (BadSignature, AssertionError):
    return HttpResponse('Страница не найдена'.encode())

  log('[GET money_table2]', req.GET)

  if 'download' in req.GET:
    return orders_file(req, f'{id}:{code}')

  album = Album(session, sh, shyear, group, after=req.GET.get('after',''))

  return render(req, 'money_table2.html', {'album':album})


def money_table(request, session, sh, year, group, code):

  sign = f'{session}__{sh}_{year}{group}:{code}'
  cls = f'{year}{group.upper()}'

  try:
    unsigned = signer.unsign(sign)

  except BadSignature:
    return HttpResponse('Код неверный'.encode())

  after = None
  if request.GET.get('after'):
    y,m,d = map(int, request.GET['after'].split('-')[:3])
    after = datetime.now().replace(year=y, month=m, day=d, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

  table = []
  total = {'name': 'ВСЕГО', 'sum': 0, 'img':''}


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


  for file in (settings.MEDIA_ROOT / 'orders').iterdir():
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

  for SH in (settings.MEDIA_ROOT / 'blanks').iterdir():
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


def orders_file(req, sign, format='excel'):
  album = Album.from_sign(sign, after=req.GET.get('after', ''))

  if format == 'json':
    content = json.dumps(album.get_money_table(), ensure_ascii=False)
    filename = f"{album.id}.json"
  elif format == 'excel':
    content = album.get_csv_content()
    filename = f"{album.id}.csv"

  res = HttpResponse(content, content_type='application/text charset=utf-8')
  res['Content-Disposition'] = f'attachment; filename="{filename}"'.encode()

  return res


def to_csv_order(data):

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
    return HttpResponse('Код неверный'.encode())

  after = []
  if request.GET.get('after'):
    y,m,d = map(int, request.GET['after'].split('-')[:3])
    after = datetime.now().replace(year=y, month=m, day=d, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

  content = []

  for file in (settings.MEDIA_ROOT / 'orders').iterdir():
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

