# coding=utf-8
from django.conf import settings

def log(*args, **kw):
 if settings.DEBUG:
   print(*args, **kw)
