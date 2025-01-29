# coding=utf-8
import pickle, json

from django.core.signing import Signer, BadSignature
from django.urls import reverse
from django.conf import settings


from utils import log


signer = Signer()
ALBUMS = settings.MEDIA_ROOT / 'users' / '1' / 'albums'


def read_table(pathfile):
 if pathfile.is_file():
   lines = pathfile.read_text(encoding='utf-8').split('\n')
   lines = [[i.strip() for i in l.split(';')] for l in lines if l.strip()]
   return lines
 return []

def write_table(pathfile, table):
 raw = '\n'.join(';'.join(i.strip() for i in line) for line in table if line)
 pathfile.write_text(raw, encoding='utf-8')



def read_order(pathfile, format='json'):
  # -> dict
  if format in ('pkl', 'pickle'):
    with pathfile.open('rb') as f:
      return pickle.load(f)

  elif format == 'json':
    with pathfile.open('r', encoding='utf8') as f:
      return json.load(f)

  raise ValueError('format must be json|pkl|pickle')

def save_order(pathfile, obj, format='json'):
  if format in ('pkl', 'pickle'):
    with pathfile.open('wb') as f:
      return pickle.dump(obj, f)

  elif format == 'json':
    with pathfile.open('w', encoding='utf8') as f:
      return json.dump(obj, f, ensure_ascii=False)

  raise ValueError('format must be json|pkl|pickle')



def read_users(ALBUM):
  file = ALBUM / 'users.json'
  if not file.is_file():
    return {}
  raw = file.read_text(encoding='utf-8')
  data = json.loads(raw)
  return data

def write_users(ALBUM, users_dict):
  file = ALBUM / 'users.json'
  if 'ver' not in users_dict:
    users_dict['ver'] = '1'
  file.write_text(json.dumps(users_dict), encoding='utf-8')



def read_album3(ALBUM, user, signer=signer, items=['kadr', 'names'], users_json=None, uuser=None):

  PORTS = ALBUM / 'ports'
  ports = {}
  for uu in PORTS.iterdir():
    f = next(uu.glob('*.jpg'), None)
    if f and f.is_file():
      ports[uu.name] = {
        'imgname':f.name,
        'src':f'/media/users/{user}/albums/{ALBUM.name}/ports/{uu.name}/{f.name}',
      }
  ports = dict(sorted(ports.items(), key=lambda i:i[1]['imgname']))

  MINI = ALBUM / 'mini'
  for f in MINI.glob('*.jpg'):
    uu = f.name[:-4]
    if uu in ports:
      ports[uu]['mininame'] = f.name
      ports[uu]['minisrc'] = f'/media/users/{user}/albums/{ALBUM.name}/mini/{f.name}'

  item_count = {}
  for item, filename, k in [
    ('names', 'names.csv', 'name'),
    ('kadr', 'guides.csv', 'guides'),
  ]:
    item_count[item] = 0
    file = ALBUM / filename
    table = read_table(file)
    for uu, imgname, *data in table:
      if uu not in ports: continue
      value = ';'.join(data).strip()
      if not value: continue
      ports[uu][k] = value
      item_count[item] += 1

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

  tmp = {
    'user': user,
    'album': ALBUM.name,
    'name': ALBUM.name,
    'ports': ports,
    'signed_url': {},
    'offer': {},
    'item_user': {},
  }

  users_json = users_json or read_users(ALBUM)

  for item in ['names', 'kadr']:
    if item not in items: continue

    url = reverse('kadr_signed', args=[signer.sign(f'user={user};album={ALBUM.name};view={item}')])

    tmp['signed_url'][item] = url

    item_roles = [r for r, its in users_json.get('offer',{}).get('role',{}).items() if item in its]

    item_users = users_json.get('offer',{}).get('user',{}).get(item,[])

    tmp['offer'].setdefault('roles',{})[item] = item_roles
    tmp['offer'].setdefault('users',{})[item] = item_users

    item_user = users_json.get('user',{}).get(item)
    if item_user:
      tmp['item_user'][item] = item_user

    tmp.update({
      f'{item}_done': f'{item_count[item]} / {ports_count}',
      f'{item}_progress': item_count[item] / ports_count * 100,
      f'url_signed_{item}': url,
      f'{item}_user': item_user,
      f'{item}_roles': item_roles,
      f'{item}_users': item_users,
    })

  return tmp





def get_user_key(uu, key, default=None):
  file = next((settings.MEDIA_ROOT / 'users' / uu).glob(f'{key}=*'), None)
  if file is None:
    return default
  return file.name.split('=')[-1]



def add_roles_offer(album, item, role):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  data = read_users(ALBUM)
  if item in data.get('offer',{}).get('role',{}).get(role,[]):
    return True
  data.setdefault('offer',{}).setdefault('role',{}).setdefault(role,[]).append(item)
  write_users(ALBUM, data)
  return True

def remove_roles_offer(album, item, role):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  data = read_users(ALBUM)
  if item not in data.get('offer',{}).get('role',{}).get(role,[]):
    return True
  data['offer']['role'][role] = [i for i in data['offer']['role'][role] if i!=item]
  write_users(ALBUM, data)
  return True

def add_users_offer(album, item, user):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  data = read_users(ALBUM)
  if user in data.get('offer',{}).get('user',{}).get(item,[]):
    return True
  data.setdefault('offer',{}).setdefault('user',{}).setdefault(item,[]).append(user)
  write_users(ALBUM, data)
  return True

def remove_users_offer(album, item, user):
  ALBUM = ALBUMS / album
  if not ALBUM.is_dir(): return False
  data = read_users(ALBUM)
  if user not in data.get('offer',{}).get('user',{}).get(item,[]):
    return True
  data['offer']['user'][item] = [i for i in data['offer']['user'][item] if i != user]
  write_users(ALBUM, data)
  return True

def set_album_offer(action, group, album, item, value):
  return {('add', 'roles'):add_roles_offer,
  ('add', 'users'):add_users_offer,
  ('remove', 'roles'):remove_roles_offer,
  ('remove', 'users'):remove_users_offer}[action, group](album, item, value)



def set_task_user(album, item, role, uu):
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

def unset_task_user(album, item, role, uu):
 ALBUM = ALBUMS / album
 if not ALBUM.is_dir(): return False
 users = read_users(ALBUM)

 user_item_uu = users.get('user',{}).get(item)

 if user_item_uu != uu:
   return True

 del users['user'][item]
 write_users(ALBUM, users)
 return True






