from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from foto import views

urlpatterns = [
    path('zakaz/<str:session>__<str:sh>_<int:shyear><str:group>/<uuid:uuid>/', views.zakaz, name='zakaz'),

    path('<str:session>__<str:sh>_<int:year><str:group>:<str:code>/', views.signed_view, name="signed_view"),

    # http://83.220.168.4/4_1%D0%90:agBVmO1xRZTnMNNwoXg8UBidjXaAv8MSLV0TsdV_gmA/
    path('upload_blanks/7f094d61-bb45-4375-81fe-32fcbb383d5c/', views.upload_blanks, name='upload_blanks'),

    path('manage_blanks/bdadc1ad-ebc7-4671-a990-5d223bf913d8/', views.manage_blanks, name='manage_blanks'),

    path('orders/3528ca60-28b5-49d1-8574-66897823a017/', views.orders, name='orders'),

    path('money_table/<str:sh>_<int:year><str:group>:<str:code>/', views.money_table, name='money_table'),

    path('<str:code>/<str:session>__<str:sh>_<int:shyear><str:group>/money_table/', views.money_table2, name='money_table2'),

    path('download_orders/<str:sh_cls>:<str:code>/', views.download_orders, name='download_orders'),

    # kadr
    path('kadr/', include('kadr.urls')),

    path('work/', include('work.urls')),

    path('admin/', admin.site.urls),

    # path('play/', views.play, name='play'),
    path('play/', include('play.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
