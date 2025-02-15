from django.urls import path

from . import views


urlpatterns = [
  # path('', views.main, name="kadr_main"),

  path('users/<str:user>/albums/', views.kadr_albums, name="kadr_albums"),

  path('users/<str:user>/albums/<str:album>/', views.kadr_main, name="kadr_main"),

  path('users/<str:user>/albums/<str:album>/names/', views.kadr_names, name="kadr_names"),

  path('signed/<str:code>/', views.kadr_signed, name="kadr_signed"),
]

