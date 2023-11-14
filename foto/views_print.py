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

from .models import Company


def index(request):



  return render(request, 'index.html', {
    'companies': Company.objects.filter(visible=True, active=True)
  })


def zakaz_index(request):

  data = [
    {"sh": 91, "title": "Школа 91", "classes": ["1А", '1Б']},
    {"sh": 158, "title": "Школа 158", "classes": ["1И", '10Б']},
  ]

  return render(request, 'zakaz_index.html', {
    "data": json.dumps(data, ensure_ascii=False),
  })


def get_uuid(request):
  return JsonResponse({
    'uuid': uuid4(),
  })


def print_view(request):

  studio_id = request.GET.get('studio')
  studio = None
  if studio_id:
    studio = Company.objects.get(id=studio_id)

  return render(request, 'print.html', {
    # 'items': [
    #   f for f in os.listdir('media/ports')
    #   if os.path.isfile(os.path.join('media', 'ports', f))
    # ],
    'folder': 'media/user_imgs',
    'studio': studio,
  })


def get_user_imgs(request):

  if request.method == 'POST':
    # print(request.POST)
    # print(request.body)
    data = json.loads(request.body)
    uuid = data.get('uuid')

    if not uuid:
      return JsonResponse({'status':'FAIL', 'msg': 'empty uuid'})

    uuid = uuid.split('-')
    user_dir = os.path.join('media', 'user_imgs', *uuid)
    files = os.listdir(user_dir)
    items = []

    for file in files:
      width, height, *_ = file.split('_')
      width = int(width)
      height = int(height)
      items.append({
        'naturalWidth': width,
        'naturalHeight': height,
        'src': os.path.join('/'+user_dir, file),
        'filename': file,
        'asp': width/height,
        'q': 1,
        'paper': 'L',
        'size': [152,102] if width > height else [102,152],
        'crop': {'width': '100%', 'left': '0%', 'top':'0%'},
      })

    return JsonResponse({
      'status': 'OK',
      'items': items,
    })


def handle_file_upload(file, uuid, width, height, filename):
  uuid = uuid.split('-')
  user_dir = os.path.join('media', 'user_imgs', *uuid)

  if not os.path.isdir(user_dir):
    os.makedirs(user_dir)

  trg_file = os.path.join(user_dir, f'{width}_{height}_{uuid4()}{os.path.splitext(filename)[-1]}')

  with open(trg_file, 'wb+') as f:
    for chunk in file.chunks():
      f.write(chunk)

  return trg_file


def upload_file(request):

  if request.method == 'POST':
    file = request.FILES.get('file')

    if file:
      link = handle_file_upload(
        file,
        request.POST.get('uuid'),
        request.POST.get('width'),
        request.POST.get('height'),
        request.POST.get('filename'),
      )

      return JsonResponse({
        'status': 'OK',
        'item': {'src': '/' + link},
      })

  return JsonResponse({'status': 'FAIL', 'msg': 'not POST or no file'})

