from django.shortcuts import render
from django.conf import settings


# Create your views here.
def main(req, user, album):

  ALBUM = settings.MEDIA_ROOT / 'users' / user / 'albums' / album
  PORTS = ALBUM / 'ports'
  KADR = ALBUM / 'kadr'

  ports = []

  if PORTS.exists():
    for uu in PORTS.iterdir():
      img = None
      mini = None
      for f in uu.iterdir():
        if f.name.endswith('_mini.jpg'): mini = f
        else: img = f
      if img:
        if mini is None: mini = img
        ports.append({
          'src': f'/media/users/{user}/albums/{album}/ports/{uu.name}/{img.name}',
          'mini': f'/media/users/{user}/albums/{album}/ports/{uu.name}/{mini.name}',
        })


  return render(req, 'kadr/main.html', {
    'ports': ports,
  })
