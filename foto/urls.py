from django.urls import path


from .views import *


urlpatterns = [
  path('manage_albums/bdadc1ad-ebc7-4671-a990-5d223bf913d8/', manage_albums, name='manage_blanks'),
  path('<str:sign>/blanks/', blanks, name='blanks'),
  path('<str:sign>/order/<int:id>/', order, name='order'),
]
