from django.core import management

from foto.album import Album as A
from foto.models import Session, Album, Order

class Command(management.BaseCommand):

  def handle(self, *args, **opts):
    aa = A.get_albums()

    for a in aa:
      print(a)
      year, _, name = a.session.partition('_')
      year = int(year)

      ses, is_new = Session.objects.get_or_create(
        year=year,
        name=name,
        defaults={'pricelist':a.get_empty_goods()},
      )

      print(is_new, ses)

      alb, is_new = Album.objects.get_or_create(
        session=ses,
        sh=a.sh,
        shyear=a.shyear,
        group=a.group,
        defaults={
          'closed': a.file_mtime_as_datetime(a.get_closed_file()) if a.is_closed else None,
          'deleted': a.file_mtime_as_datetime(a.get_deleted_file()) if a.is_deleted else None,
        },
      )

      print(is_new, alb)
