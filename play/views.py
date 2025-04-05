import json

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from utils import log


def main(req):

  if req.method == 'POST' and req.FILES.get('file'):
    return upload(req)

  fonts = [
    [d.name, [f.name for f in d.iterdir() if f.is_file() and f.suffix in ('.ttf', '.woff', '.woff2')]]
    for d in (settings.BASE_DIR / 'static' / 'fonts').iterdir()
    if d.is_dir()
  ]

  return render(req, 'play/main.html', {
    'fonts': fonts,
    'document': (settings.BASE_DIR / 'media' / 'doc.json').read_text(),
  })



def api_get_font(req, family, style='Regular'):
  log('[api_get_font]', req)

  fonts = settings.BASE_DIR / 'static' / 'fonts'

  family = family.lower()
  style = style.lower()

  def search_dir(d):
    match = None
    for f in d.iterdir():
      if f.name[0] == '.': continue
      if f.is_file():
        if f.suffix not in ('.ttf', '.woff', '.woff2'): continue
        if family in f.stem.lower():
          if style in f.stem.lower() or match is None:
            match = f

      else:
        res = search_dir(f)
        if res:
          return res

    return match

  font = search_dir(fonts)

  return redirect(f'/static/fonts/{font.relative_to(fonts)}')



def upload(req):
  if req.method == 'POST' and req.FILES.get('file'):
    file = req.FILES['file']
    trg_file = settings.MEDIA_ROOT / file.name
    with trg_file.open('wb') as f:
      for ch in file.chunks():
        f.write(ch)
    return JsonResponse({'status': 'OK', 'src': f'/media/{file.name}'})

  return JsonResponse({'status': 'DEFAULT'})



def save_document(req):
  if req.method != 'POST':
    return HttpResponse('Wrong Method'.encode())

  log(f'{req.body=}')

  data = json.loads(req.body)

  trg = settings.BASE_DIR / 'media' / 'doc.json'

  trg.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

  return JsonResponse({'status': 'OK'})


