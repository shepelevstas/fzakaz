from django.urls import path

from . import views

urlpatterns = [
    path('', views.main, name='play_main'),
    path('save/', views.save_document, name='save_document'),
    path('api/get_font/<str:family>/<str:style>/', views.api_get_font, name='api_get_font'),
]
