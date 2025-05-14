# coding=utf-8
from django.conf import settings

def log(*args, **kw):
  if settings.DEBUG:
     print(*args, **kw)


def is_htmx(req):
  return req.headers.get('HX-Request') == 'true'
