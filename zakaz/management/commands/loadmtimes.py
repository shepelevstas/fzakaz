from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from re import compile as re
from zakaz.models import Session, Album, Blank, Pricelist
from zakaz.utils import translit
import json


group_dir = re(r'(\d+)?(\w)')

class Command(BaseCommand):
    def handle(self, *args, **options):

        mtfile = settings.MEDIA_ROOT / 'orders' / 'mtimes.json'
        data = json.loads(mtfile.read_text())

        for item in data:
            [ses_year, s, ses_name] = item['ses'].partition('_')
            ses_year = int(ses_year)

            ses = Session.objects.get(year=ses_year, name=ses_name)

            sh = item['sh']

            try:
                yr = int(item['group'][:-1])
                gr = item['group'][-1]
            except ValueError:
                if item['group'] == 'd' and item['sh'] == 90:
                    yr = 2
                    gr = 'd'
                else:
                    print(f'ValueError on {item["group"]}')
                    print(item)
                    break

            gr = gr.translate(translit)

            try:
                alb = Album.objects.get(session=ses, sh=sh, year=yr, group=gr)
            except Album.DoesNotExist:
                print(f'Album not found: ses:{ses}, sh:{sh}, year:{yr}, group:{gr}')
                break

            try:
                blk = Blank.objects.get(album=alb, imgname=item['blank'], ordered=None)
            except Blank.DoesNotExist:
                continue

            if blk:
                blk.ordered = datetime.fromisoformat(item['mtime'])
                blk.save()
