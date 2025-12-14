from django.conf import settings
from django.core.management.base import BaseCommand
from re import compile as re
from zakaz.models import Session, Album, Blank, Pricelist
import json


group_dir = re(r'(\d+)?(\w)')
translit = str.maketrans(
  'фотхмагнипдушкржблв еёзсчцщюыъьэяй',
  "fotxmagnipdyskrjblv_eezs4csui''qji"
)


class Command(BaseCommand):
    def handle(self, *args, **options):

        files = len(list((settings.MEDIA_ROOT / 'orders').glob('**/*.json')))
        print(f'json files count: {files}')
        done = 0

        ORDERS = settings.MEDIA_ROOT / 'orders'

        for SES in ORDERS.iterdir():
            if not SES.is_dir() or '_' not in SES.name: continue
            
            [ses_year, s, ses_name] = SES.name.partition('_')
            price_name = (SES / 'price').read_text().strip()
            print(f'PRICE: {price_name}')
            pricelist = Pricelist.objects.get(name=price_name)
            ses, ses_is_new = Session.objects.get_or_create(
                name=ses_name,
                year=int(ses_year),
                pricelist=pricelist,
            )

            for SH in SES.iterdir():
                if not SH.is_dir() or not SH.name.isdigit(): continue

                for CLS in SH.iterdir():
                    if not CLS.is_dir(): continue
                    mo = group_dir.match(CLS.name)
                    if not mo: continue

                    alb, alb_is_new = Album.objects.get_or_create(
                        sh=SH.name,
                        year=int(mo[1]) if mo[1] else 0,
                        group=mo[2].lower().translate(translit) if mo[2] else "",
                        session=ses,
                    )

                    for file in CLS.iterdir():
                        if not file.is_file() or not file.name.endswith('.json'): continue

                        blank, is_new = Blank.objects.get_or_create(
                            album=alb,
                            imgname=file.stem,
                            defaults={
                                'order': json.loads(file.read_text()),
                                'img': None,
                            }
                        )

                        if is_new:
                            print(f'{SES.name}/{SH.name}/{CLS.name}/{file.name}')
                            done += 1

        print(f'found files: {files}, done: {done}')
