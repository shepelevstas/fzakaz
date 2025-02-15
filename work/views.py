# coding=utf-8
from django.conf import settings
from django.shortcuts import render, HttpResponse
from django.urls import reverse
from django.core.signing import Signer, BadSignature

from utils import log, is_htmx
from utils.io import read_users, write_users, read_album3, get_user_key, set_task_user, unset_task_user


signer = Signer()
ALBUMS = settings.MEDIA_ROOT / 'users' / '1' / 'albums'



def take_user(album, item, uu, role):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  users = read_users(ALBUM)

  user_item_uu = users.get('user',{}).get(item)
  if user_item_uu == uu:
    return True

  if user_item_uu is not None:
    return False

  item_in_role = item in users.get('offer',{}).get('role',{}).get(role,[])
  if item_in_role:
    users.setdefault('user',{})[item] = uu
    write_users(ALBUM, users)
    return True

  uu_in_item = uu in users.get('offer',{}).get('user',{}).get(item,[])
  if uu_in_item:
    users.setdefault('user',{})[item] = uu
    write_users(ALBUM, users)
    return True

  return False

def giveup_user(album, item, uu, role):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  users = read_users(ALBUM)

  user_item_uu = users.get('user',{}).get(item)

  if user_item_uu != uu:
    return True

  del users['user'][item]
  write_users(ALBUM, users)
  return True

user_actions = {'take_user': take_user, 'giveup_user': giveup_user}



def work(req, uu):
  log('[ POST ]', req.POST)

  role = get_user_key(uu, 'role', 'worker')

  if req.method == 'POST':
    action = req.POST.get('action')
    album = req.POST.get('album')
    item = req.POST.get('item')

    if action in user_actions and album and item in ("kadr", "names"):
      success = user_actions[action](album, item, uu, role)
      if is_htmx(req):
        if success:

          next_action = {"take_user":"giveup_user", "giveup_user":"take_user"}[action]
          link_color = {"take_user":"secondary", "giveup_user":"primary"}[next_action]
          link_name = {"kadr":"Кадр", "names":"Имена"}[item]
          btn_color = {"take_user":"success", "giveup_user":"danger"}[next_action]
          btn_name = {"take_user":"Взять", "giveup_user":"Отказаться"}[next_action]

          url_signed = reverse('kadr_signed', args=[signer.sign(f'user=1;album={album};view={item}')]) if action == 'take_user' else "#"

          return HttpResponse(f'''
            <a href="{url_signed}" class="btn btn-outline-{link_color}">{link_name}</a>
            <button
              class="btn btn-outline-{btn_color}"
              hx-post="{req.path}"
              hx-headers='js:{{"X-CSRFToken": getCookie("csrftoken")}}'
              hx-target="closest .btn-group"
              name="action"
              value="{next_action}"
              hx-vals='{{"album":"{album}","htmx":true,"item":"{item}"}}'
            >{btn_name}</button>
          ''')
        else:
          return HttpResponse(f'''
            <button class="btn btn-outline-danger" disabled="true">
              Закрыто
            </button>
          ''')

  username = get_user_key(uu, 'name', 'NoName')

  data = []

  for ALBUM in ALBUMS.iterdir():
    if not ALBUM.is_dir(): continue
    users = read_users(ALBUM)

    kadr_user = None
    kadr = None
    names_user = None
    names = None

    if users.get('ver') == '1':
      log('[ VER 1 ]')
      kadr_user = users.get('user',{}).get("kadr")
      kadr = kadr_user in (None, uu) and ('kadr' in users.get('offer',{}).get('role',{}).get(role,[]) or uu in users.get('offer',{}).get('user',{}).get('kadr',[]))

      names_user = users.get('user',{}).get("names")
      names = names_user in (None, uu) and ('names' in users.get('offer',{}).get('role',{}).get(role,[]) or uu in users.get('offer',{}).get('user',{}).get('names',[]))

    log('[ ALBUM ]', ALBUM)
    if not any([kadr, names]):
      log('[ SKIP ]')
      continue

    items = []
    if kadr: items.append('kadr')
    if names: items.append('names')

    album = read_album3(ALBUM, '1', items=items, users_json=users, uuser=uu)

    album['kadr_user_is_me'] = album.get('kadr_user') == uu
    album['names_user_is_me'] = album.get('names_user') == uu
    # album['username'] = username

    data.append(album)

  return render(req, 'kadr/kadr_albums.html', {
    'data': data,
    'form': None,
    'user': '1',
    'role': role,
    'username': username,
  })
