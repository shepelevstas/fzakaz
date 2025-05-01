from django.core import management
from django.conf import settings

from foto.album import Album as A, PriceList
from foto.models import Session, Album, Order, Pricelist


class Command(management.BaseCommand):

  def handle(self, *args, **opts):
    aa = A.get_albums()

    for a in aa:
      print(a)
      year, _, name = a.session.partition('_')
      year = int(year)

      pl = PriceList(a.get_empty_goods())

      pricelist, pricelist_is_new = Pricelist.objects.get_or_create(
        formats=pl.get_formats(),
        themes=pl.get_themes(),
        bonus=pl.get_bonus(),
        defaults={
          'name': pl.data.get('ru') or pl.data.get('en') or a.get_pricename(),
        },
      )

      ses, is_new = Session.objects.get_or_create(
        year=year,
        name=name,
        defaults={
          # 'pricelist':a.get_empty_goods(),
          'pricelist': pricelist,
        },
      )

      print('[ses]', '+' if is_new else '=', ses)

      alb, is_new = Album.objects.get_or_create(
        session=ses,
        sh=a.sh,
        shyear=a.shyear,
        group=a.group.upper(),
        defaults={
          'closed': a.file_mtime_as_datetime(a.get_closed_file()) if a.is_closed else None,
          'deleted': a.file_mtime_as_datetime(a.get_deleted_file()) if a.is_deleted else None,
        },
      )

      print('[alb]', '+' if is_new else '=', alb)

      for b in a.blanks:
        print('[BLANK]', b)
        blank = a.get_blank_file(uuid=b['uuid']) or None
        blank = str(blank.relative_to(settings.MEDIA_ROOT)) if blank else None

        order, is_new = Order.objects.get_or_create(
          album=alb,
          blank=blank,
          imgname=blank.rsplit('/', 1)[-1].rsplit('.', 1)[-2] if blank else '',
          ordered=a.get_order_time(uuid=b['uuid']) or None,
          defaults={
            'json': a.get_order(uuid=b['uuid']),
          },
        )

        print('[ord]', '+' if is_new else '=', order)

      print()