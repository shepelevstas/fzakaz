from django.urls import path

from .views import *

urlpatterns = [
    path('3528ca60-28b5-49d1-8574-66897823a017/', index, name="index"),
    path('album/<str:sign>/', album, name="album"),
    path('blank/<str:sign>/', blank, name="blank"),
    path('table/<int:id>/', table, name="table"),
    path('3528ca60-28b5-49d1-8574-66897823a017/pricelists/', pricelists, name='pricelists'),
]
