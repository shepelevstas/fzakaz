# coding=utf-8
import json
from uuid import uuid4

from PIL import Image

from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.urls import reverse

from utils import log, is_htmx
from utils.io import read_album3, get_user_key, read_users, write_users, set_task_user, unset_task_user, set_album_offer

from . import forms


signer = Signer()
ALBUMS = settings.MEDIA_ROOT / 'users' / '1' / 'albums'


def read_ports(PORTS, user, album, kadr_data, MINI=None):
  ports = []

  if PORTS.exists():
    mini_exists = MINI.exists() if MINI else False
    for uu in PORTS.iterdir():
      img = None
      mini = None

      for f in uu.iterdir():
        if f.name.endswith('.jpg'):
          img = f
          break

      if img and mini_exists and (MINI / img.name).exists():
        mini = MINI / img.name

      if img:
        src = f'/media/users/{user}/albums/{album}/ports/{uu.name}/{img.name}'
        ports.append({
          'src': src,
          'name': img.name,
          'mini': f'/media/users/{user}/albums/{album}/mini/{mini.name}' if mini else src,
          'kadr_data': kadr_data.get(img.name, ''),
        })

  ports.sort(key=lambda i: i['name'])

  return ports

def read_ports2(ALBUM, user, kadr_data, MINI=None):
  ports = []
  PORTS = ALBUM / 'ports'
  if MINI is None: MINI = ALBUM / 'mini'
  if not PORTS.is_dir(): return ports
  mini_exists = MINI.is_dir()
  for uu in PORTS.iterdir():
    img = None
    mini = None
    for f in uu.iterdir():
      if f.name.endswith('.jpg'):
        img = f
        break
    if img and mini_exists and (MINI / img.name).is_file():
      mini = MINI / img.name
    if img:
      src = f'/media/users/{user}/albums/{ALBUM.name}/ports/{uu.name}/{img.name}'
      ports.append({
        'src': src,
        'name': img.name,
        'mini': f'/media/users/{user}/albums/{ALBUM.name}/mini/{mini.name}' if mini else src,
        'kadr_data': kadr_data.get(img.name, ''),
      })
  ports.sort(key=lambda i:i['name'])
  return ports

def read_table(pathfile):
  if pathfile.is_file():
    lines = pathfile.read_text(encoding='utf-8').split('\n')
    lines = [[i.strip() for i in l.split(';')] for l in lines if l.strip()]
    return lines
  return []

def write_table(pathfile, table):
  raw = '\n'.join(';'.join(i.strip() for i in line) for line in table if line)
  pathfile.write_text(raw, encoding='utf-8')

def read_guides(guides_file):
  # kadr_data :: {<img name>::str : <raw kadr data>::str}
  # <img name> ~ SKY_0002.jpg
  # <raw kadr data> ~ "SKY_0002.jpg;0.22;0.5;0.56"
  table = read_table(guides_file)
  kadr_data = {l[0]:';'.join(l) for l in table if len(l)>3}

  return kadr_data

def read_guides2(ALBUM):
  # kadr_data :: {<img name>::str : <raw kadr data>::str}
  # <img name> ~ SKY_0002.jpg
  # <raw kadr data> ~ "SKY_0002.jpg;0.22;0.5;0.56"
  file = ALBUM / 'guides.csv'
  if not file.is_file(): return {}
  table = read_table(file)
  kadr_data = {l[0]:';'.join(l) for l in table if len(l)>3}

  return kadr_data

def read_album2(ALBUM, user, signer=signer):
  guides = ALBUM / 'guides.csv'
  names = ALBUM / 'names.csv'
  PORTS = ALBUM / 'ports'
  MINI = ALBUM / 'mini'

  ports = {}
  for uu in PORTS.iterdir():
    f = next(uu.glob('*.jpg'))
    if f and f.is_file():
      ports[uu.name] = {
        'imgname':f.name,
        'src':f'/media/users/{user}/albums/{ALBUM.name}/ports/{uu.name}/{f.name}',
      }
  ports = dict(sorted(ports.items(), key=lambda i:i[1]['imgname']))

  for f in MINI.glob('*.jpg'):
    uu = f.name[:-4]
    if uu in ports:
      ports[uu]['mininame'] = f.name
      ports[uu]['minisrc'] = f'/media/users/{user}/albums/{ALBUM.name}/mini/{f.name}'

  names_table = read_table(names)
  for uu, imgname, name in names_table:
    if uu in ports:
      ports[uu]['name'] = name

  guides_table = read_table(guides)
  for uu, imgname, top, bot, mid in guides_table:
    if uu in ports:
      ports[uu]['guides'] = ';'.join([top,bot,mid])

  ''' ports :: {<uuid>: <port>}
    port :: {
      'imgname' :: str
      'src' :: str
      'mininame' :: str
      'minisrc' :: str
      'name' :: str
      'guides' :: str
    }
  '''

  ports_count = len(ports)
  # kadr_count = len([None for p in ports if 'guides' in p])
  # names_count = len([None for p in ports if 'name' in p and p['name']])
  kadr_count = 0
  names_count = 0
  for uu, p in ports.items():
    if 'guides' in p and p['guides']:
      kadr_count += 1
    if 'name' in p and p['name']:
      names_count += 1

  # log('[ PORTS ]', ports)

  return {
    'user': user,
    'album': ALBUM.name,

    'ports': ports,

    'names_done': f'{names_count} / {ports_count}',
    'names_progress': names_count / ports_count * 100,
    'url_signed_names': reverse('kadr_signed', args=[signer.sign(f'user={user};album={ALBUM.name};view=names')]),

    'kadr_done': f'{kadr_count} / {ports_count}',
    'kadr_progress': kadr_count / ports_count * 100,
    'url_signed_kadr': reverse('kadr_signed', args=[signer.sign(f'user={user};album={ALBUM.name};view=kadr')]),
  }

def write_guides3(ALBUM, uuid, img, data):
  guides = ALBUM / 'guides.csv'
  if not ALBUM.is_dir(): ALBUM.mkdir(parents=True, exist_ok=True)

  table = read_table(guides)

  # table = [l for l in table if l[0]!=uuid or l[1]!=img]
  # table.append([uuid, img, data])
  # table.sort(key=lambda l:l[0])
  # write_table(guides, table)

  new_table = []
  updated = False
  for l in table:
    if uuid == l[0] and img == l[1]:
      new_table.append([uuid, img, data])
      updated = True
    else:
      new_table.append(l)

  if not updated:
    new_table.append([uuid, img, data])

  write_table(guides, new_table)

def write_guides2(ALBUM, data, line=None):
  ''' data :: {<img file name> : <raw line data>}
  '''
  file = ALBUM / 'guides.csv'
  if not ALBUM.is_dir():
    ALBUM.mkdir(parents=True, exist_ok=True)

  if line is not None:
    cells = line.split(';')
    if len(cells) == 4:
      data[cells[0].strip()] = line

  raw = '\n'.join(data.values())
  file.write_text(raw, encoding='utf-8')

def read_names(ALBUM):
  if not ALBUM.is_dir(): return {}
  table = read_table(ALBUM / 'names.csv')
  data = {l[0]:l[1] for l in table if len(l)>1}

  return data

def write_names(ALBUM, names_dict):
  raw = '\n'.join(f'{fn};{nm}' for fn,nm in names_dict.items())
  file = ALBUM / 'names.csv'
  file.write_text(raw, encoding='utf-8')

def write_names2(ALBUM, ports_dict):
  file = ALBUM / 'names.csv'
  table = []
  for uu, p in ports_dict.items():
    table.append([
      uu, p['imgname'], p['name']
    ])
  write_table(file, table)

def read_album(ALBUM, user, signer):
  ''' data = [
      { 'album': '2023_2024_18_1A',
        'kadr': '2 / 2',
        'progress': 100,
        'url_signed_names': 'user=1;album=2023_2024_18_1A;view=names'
        'url_signed_kadr': 'user=1;album=2023_2024_18_1A;view=kadr'
      },]
  '''
  kadr_data = read_guides2(ALBUM)
  ports = read_ports2(ALBUM, user, kadr_data)
  names = read_names(ALBUM)

  return {
    'album': ALBUM.name,

    'names': f'{len(names)} / {len(ports)}',
    'names_progress': len(names) / len(ports) * 100,

    'kadr': f'{len(kadr_data)} / {len(ports)}',
    'progress': len(kadr_data) / len(ports) * 100,

    'url_signed_names': reverse('kadr_signed', args=[signer.sign(f'user={user};album={ALBUM.name};view=names')]),
    'url_signed_kadr': reverse('kadr_signed', args=[signer.sign(f'user={user};album={ALBUM.name};view=kadr')]),
  }


def users_list():
  tmp = []  # :: [[<user uuid>, <role>, <username>]]
  for uu in (settings.MEDIA_ROOT / 'users').iterdir():
    if not uu.is_dir(): continue
    if uu.name == '1': continue
    role = get_user_key(uu.name, 'role', 'worker')
    if role != 'worker': continue
    name = get_user_key(uu.name, 'name', 'NoName')
    tmp.append([uu.name, role, name])
  return tmp



def upload_to_album(req):
  form1 = forms.UploadAlbumForm(req.POST, req.FILES)
  if form1.is_valid():
    album = form1.cleaned_data['album'].strip().upper()
    ALBUM = ALBUMS / album
    is_new = not ALBUM.is_dir()
    MINI = ALBUM / 'mini'
    MINI.mkdir(parents=True, exist_ok=True)
    PORTS = ALBUM / 'ports'
    water = Image.open(settings.BASE_DIR / 'static' / 'water.png')

    for file in req.FILES.getlist('files'):
      uu = str(uuid4())
      PORT = PORTS / uu
      PORT.mkdir(parents=True, exist_ok=True)
      trg_file = PORT / file.name
      with trg_file.open('wb') as f:
        for ch in file.chunks():
          f.write(ch)

      im = Image.open(trg_file)
      w, h = im.size
      LONG_SIDE = 600
      if w > h: w, h = LONG_SIDE, round(LONG_SIDE / w * h)
      else: w, h = round(LONG_SIDE / h * w), LONG_SIDE
      mini = im.resize((w, h))
      mini_trg = MINI / f'{uu}.jpg'
      mini.save(mini_trg, quality=40, optimize=True, progressive=True)
      im.paste(water, (0, 0), water)
      im.save(trg_file, quality=40, optimize=True, progressive=True)

    return (True, is_new)

  return (False, None)


def kadr_albums(req, user):
  log('[ USER ]', user)

  users = users_list()  # :: [[<user uuid>, <role>, <username>]]
  users = {uu:name for uu,role,name in users}

  groups = [
    { 'name': 'roles',
      'ru': 'Группы',
      'menu': [
        { 'name': 'worker', 'ru': 'Исполнители' },
      ],
    },
    { 'name': 'users',
      'ru': 'Люди',
      'menu': [
        { 'name': name, 'ru': username }
        for name, username in users.items()
      ],
    },
  ]

  items = [
    { 'name': 'kadr', 'ru': 'Кадр' },
    { 'name': 'names', 'ru': 'Имена' },
  ]

  if req.method == 'POST':
    log('[ POST ]', req.POST)
    action = req.POST.get('action')
    item = req.POST.get('item')    # kadr | names
    group = req.POST.get('group')  # roles | users
    album = req.POST.get('album').strip().upper()  # 2023_2024_18_1A
    exec_user = req.POST.get('user')
    ajax = req.POST.get('ajax') == 'true'

    if False and action == 'upload':
      log('[ FILES ]', req.FILES)

      succ, is_new = upload_to_album(req)

      if req.POST.get('ajax') == 'true':
        data_list = []
        for ALBUM in ALBUMS.iterdir():
          data_list.append(read_album2(ALBUM, user))
        return JsonResponse({'data_list': data_list})

    if ajax:
      if action in ('set_exec', 'unset_exec') and 'value' in req.POST:
        value = req.POST.get('value')
        succ = {'set_exec':set_task_user,'unset_exec':unset_task_user}[action](album, item, 'worker', value)
        if succ:
          return JsonResponse({'status': 'OK'})
      return JsonResponse({'status': 'FAIL'})

    if is_htmx(req):
      log('[ is htmx ]')
      if action in ('set_exec', 'unset_exec') and 'value' in req.POST:
        value = req.POST['value']
        succ = {'set_exec':set_task_user,'unset_exec':unset_task_user}[action](album, item, 'worker', value)

        if not succ:
          return HttpResponse(f'''
            <div class="d-inline-flex">
              <span class="btn badge rounded-pill text-bg-danger">ОШИБКА</span>
            </div>
          ''')

        next_action = {'set_exec':'unset_exec','unset_exec':'set_exec'}[action]
        return render(req, f"kadr/parts/kadr_albums_line_{next_action}.html", {
          'item_user': value,
          'users': users,
          'i': {'album': album},
          'item': {'name': item},
        })

      if action in ('add', 'remove') and item in ('kadr', 'names') and group in ('roles', 'users'):
        log('[ htmx ]', )
        menu_item_ru = req.POST.get('menu_item_ru')  # Исполнители | User1
        menu_item_name = req.POST.get('menu_item_name')  # worker | <uuid>

        next_action = {"add":"remove", "remove":"add"}[action]
        i_class = {"add":"bi-circle text-black-50", "remove":"bi-check-circle text-primary"}[next_action]

        succ = set_album_offer(action, group, album, item, menu_item_name)

        return HttpResponse(f'''
          <a
            class="dropdown-item"
            href="#"
            hx-post="{req.path}"
            hx-vals='{{"album":"{album}","item":"{item}","group":"{group}","action":"{next_action}","menu_item_name":"{menu_item_name}","menu_item_ru":"{menu_item_ru}"}}'
            hx-target="closest li"
          ><i class="pe-2 bi {i_class}"></i>{menu_item_ru}</a>
        ''')

      if action == 'upload':
        log('[ FILES ]', req.FILES)
        offer = req.POST.get('offer')

        succ, is_new = upload_to_album(req)

        if is_new and offer:
          for i in offer.split(';'):
            ac,gr,it,vl = i.split(',')
            set_album_offer(ac,gr,album,it,vl)

        album_data = read_album3(ALBUMS / album, user)
        res = render(req, 'kadr/parts/kadr_albums_line.html', {
          'i': album_data,
          'role': 'super',
          'items': items,
          'groups': groups,
          'users': users,
          'new_line': is_new,
        })

        res.headers['HX-Retarget'] = '#new_line' if is_new else f'tr[data-album="{album}"]'

        return res

  albums = []
  for ALBUM in ALBUMS.iterdir():
    albums.append(read_album3(ALBUM, user))

  return render(req, 'kadr/kadr_albums.html', {
    'data': albums,
    'user': user,
    'form': forms.UploadAlbumForm(),
    'role': 'super' if user == '1' else 'worker',

    'items': items,
    'groups': groups,
    'users': users,
  })


def kadr_main(req, user, album, signed=False):
  ALBUM = settings.MEDIA_ROOT / 'users' / user / 'albums' / album

  ''' ports :: {<uuid>: <port>}
    port :: {
      'imgname' :: str
      'src' :: str
      'mininame' :: str
      'minisrc' :: str
      'name' :: str
      'guides' :: str
    }
  '''

  if req.method == 'POST':
    action = req.POST.get('action')

    if action == 'save_kadr_data':
      data = req.POST.get('data', '').strip()
      uuid = req.POST.get('uuid', '').strip()
      img = req.POST.get('img', '').strip()

      log('[ SAVE DATA ]', data, uuid, img)

      if all([img, uuid, data]):
        write_guides3(ALBUM, uuid, img, data)

        return HttpResponse('OK')
      return HttpResponse('DATA LEN ERR')
    return HttpResponse('WRONG ACTION ERR')

  album_data = read_album2(ALBUM, user)

  return render(req, 'kadr/kadr_main.html', {
    'user': user,
    'album': album,
    'signed': signed,
    'ports': album_data['ports'],
  })


def kadr_names(req, user, album):
  ALBUM = settings.MEDIA_ROOT / 'users' / user / 'albums' / album
  album_data = read_album2(ALBUM, user)
  ports = album_data['ports']

  if req.method == 'POST':
    post = json.loads(req.body)
    log('[ JSON ]', post)

    if 'names' in post:
      for uu, name in post['names'].items():
        ports[uu]['name'] = name
      write_names2(ALBUM, ports)

      return HttpResponse('OK')

    return HttpResponse('FAIL')

  return render(req, 'kadr/kadr_names.html', {
    'ports': ports,
    'user': user,
    'album': album,
  })


def kadr_signed(req, code):
  log('[ PATH ]', req.path)
  # log('[ REQ ]', dir(req))

  try:
    raw = Signer().unsign(code)
  except BadSignature:
    return HttpResponse('BadSignature')

  data = dict([kv.split('=') for kv in raw.split(';')])
  log('[ DATA ]', data)
  if 'view' in data:
    if data['view'] in ('names', 'kadr_names'):
      return kadr_names(req, data['user'], data['album'])
    if data['view'] == 'albums':
      return kadr_albums(req, data['user'])
    if data['view'] == 'kadr':
      return kadr_main(req, data['user'], data['album'], True)

  return HttpResponse(raw)


