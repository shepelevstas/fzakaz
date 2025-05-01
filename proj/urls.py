from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from foto import views

urlpatterns = [
    path('', include('foto.urls')),

    path('zakaz/<str:session>__<str:sh>_<int:shyear><str:group>/<uuid:uuid>/', views.zakaz, name='zakaz'),

    path('blanks/<str:sign>/', views.signed_view, name="signed_view"),

    # http://83.220.168.4/4_1%D0%90:agBVmO1xRZTnMNNwoXg8UBidjXaAv8MSLV0TsdV_gmA/

    path('manage_blanks/bdadc1ad-ebc7-4671-a990-5d223bf913d8/', views.manage_blanks, name='manage_blanks'),

    path('orders/3528ca60-28b5-49d1-8574-66897823a017/', views.orders, name='orders'),

    path('money_table/<str:sh>_<int:year><str:group>:<str:code>/', views.money_table, name='money_table'),

    path('<str:code>/<str:session>__<str:sh>_<int:shyear><str:group>/money_table/', views.money_table2, name='money_table2'),

    path('download_orders/<str:sh_cls>:<str:code>/', views.download_orders, name='download_orders'),

    path('<str:sign>/orders_file/', views.orders_file, {'format': 'json'}, name='orders_file'),
    path('<str:sign>/excel_file/', views.orders_file, {'format': 'excel'}, name='excel_file'),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    # urlpatterns += [
    #     path('kadr/', include('kadr.urls')),
    #     path('work/', include('work.urls')),
    #     path('play/', include('play.urls')),
    # ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
