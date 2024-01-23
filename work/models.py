# coding=utf-8
from django.db import models
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from foto.models import User


class Album(models.Model):
  owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

  name = models.CharField(max_length=255)

  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField()


class Port(models.Model):
  TYPE = (
    (1, 'портрет'),
    (2, 'преподаватель'),
    (3, 'группа'),
  )

  album = models.ForeignKey(Album, on_delete=models.DO_NOTHING)

  img = models.ImageField()
  mini = models.ImageField()
  name = models.CharField(max_length=255)
  guides = models.JSONField()
  type = models.PositiveSmallIntegerField(choices=TYPE)
  mail = models.EmailField()
  tel = models.CharField(max_length=15)

  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField()


class Task(models.Model):
  TYPE = (
    (1, 'кадрирование'),
    (2, 'подпись имен'),
  )

  album = models.ForeignKey(Album, on_delete=models.DO_NOTHING)
  exec = models.ForeignKey(User, on_delete=models.DO_NOTHING)

  groups = models.ManyToManyField(Group)
  users = models.ManyToManyField(User)

  type = models.PositiveSmallIntegerField(choices=TYPE)
  done = models.DateTimeField()
  confirmed = models.DateTimeField()

  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)
  deleted = models.DateTimeField()
