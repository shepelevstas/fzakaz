from django.urls import path

from . import views


urlpatterns = [
    path('<str:uu>/', views.work, name="work"),
]
