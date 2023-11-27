from django.urls import path

from . import views


urlpatterns = [
  # path('', views.main, name="kadr_main"),
  path('users/<str:user>/albums/<str:album>/', views.main, name="kadr_main"),
]

