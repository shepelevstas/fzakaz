from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from utils import log


def main(req):

  if req.method == 'POST' and req.FILES.get('file'):
    return upload(req)

  return render(req, 'play/main.html', {})



def upload(req):
  if req.method == 'POST' and req.FILES.get('file'):
    file = req.FILES['file']
    trg_file = settings.MEDIA_ROOT / file.name
    with trg_file.open('wb') as f:
      for ch in file.chunks():
        f.write(ch)
    return JsonResponse({'status': 'OK', 'src': f'/media/{file.name}'})

  return JsonResponse({'status': 'DEFAULT'})
