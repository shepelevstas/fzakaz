import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4)
  company = models.ForeignKey('Company', on_delete=models.DO_NOTHING, null=True)


class Company(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  company = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, related_name='companies')
  name = models.CharField(max_length=128)
  city = models.CharField(max_length=128)
  address = models.CharField(max_length=512)
  tel = models.CharField(max_length=11)
  mail = models.EmailField()
  site = models.CharField(max_length=128)
  pricelist = models.JSONField()
  visible = models.BooleanField(default=True)
  active = models.BooleanField(default=True)


class Job(models.Model):
  created = models.DateTimeField(auto_now_add=True)
  company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
  user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
  prints = models.JSONField()
  status = models.PositiveSmallIntegerField()
  payed = models.DateTimeField()


