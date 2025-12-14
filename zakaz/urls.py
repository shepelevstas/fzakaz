from django.urls import path, include

from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('album/<str:sign>/', album, name="album"),
    path('blank/<str:sign>/', blank, name="blank"),
    path('pricelists/', pricelists, name='pricelists'),
]
