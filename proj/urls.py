from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static

from foto import views

urlpatterns = [
    path('zakaz/<str:sh>/<str:cls>/<uuid:uuid>/', views.zakaz, name='zakaz'),
    path('<str:sh>_<int:year><str:group>:<str:code>/', views.signed_view, name="signed_view"),

    # http://83.220.168.4/4_1%D0%90:agBVmO1xRZTnMNNwoXg8UBidjXaAv8MSLV0TsdV_gmA/
    path('upload_blanks/7f094d61-bb45-4375-81fe-32fcbb383d5c/', views.upload_blanks, name='upload_blanks'),

    path('manage_blanks/bdadc1ad-ebc6-4671-a990-5d223bf913d8/', views.manage_blanks, name='manage_blanks'),

    path('orders/3528ca60-28b5-49d1-8574-66897823a017/', views.orders, name='orders'),

    path('money_table/<str:sh>_<int:year><str:group>:<str:code>/', views.money_table, name='money_table'),

    path('download_orders/<str:sh_cls>:<str:code>/', views.download_orders, name='download_orders'),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
