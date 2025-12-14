import json
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from zakaz.models import Session, Album, Blank, Pricelist
from re import compile as re


group_dir = re(r'(\d+)?(\w)')
trans = str.maketrans(
  'фотхмагнипдушкржблв еёзсчцщюыъьэяй',
  "fotxmagnipdyskrjblv_eezs4csui''qji"
)



class Command(BaseCommand):
    def handle(self, *args, **options):

        file = settings.MEDIA_ROOT / 'blanks.json'

        lst = json.loads(file.read_text())

        data = {}
        created_list = []

        for l in lst:
            [_, ses, sh, gr, uuid, bl] = l.split('/')
            ses_yr, _, ses_nm = ses.partition('_')
            gr = gr.lower().translate(trans)
            mo = group_dir.match(gr)
            if not mo:continue
            yr = mo[1]
            gr = mo[2]
            if not yr and sh == '90' and gr == 'd':
                yr = 2
            ses = data.setdefault((ses_yr, ses_nm), {})
            imgname = bl.rsplit('.', 1)[0]
            ses.setdefault((sh, yr, gr), []).append((l, imgname))

        
        for (syr, snm), albs in data.items():
            ses = Session.objects.get(year=syr, name=snm)

            for (sh, yr, gr), blanks in albs.items():
                alb, is_new = Album.objects.get_or_create(session=ses, sh=sh, year=yr, group=gr)

                for path, bl in blanks:
                    blank = Blank.objects.get(album=alb, imgname=bl)
                    blank.img = path
                    blank.save()
                    continue
                    
                    blank, created = Blank.objects.get_or_create(
                        album=alb,
                        imgname=bl,
                    )
                    if created:
                        created_list.append(blank)
                    else:
                        blank.img = path
                        blank.save()

        print(f'created: {len(created_list)}')

                    
