from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from re import compile as re
from zakaz.models import Session, Album, Blank, Pricelist
from utils.trans import en
import json


group_dir = re(r'(\d+)?(\D)')


def file_mtime(file):
    return datetime.fromtimestamp(file.stat().st_mtime).isoformat()


ORDERS = settings.MEDIA_ROOT / 'orders'
BLANKS = settings.MEDIA_ROOT / 'blanks'


def get_blank_img(ses, sh, group, imgname):
    trgdir = BLANKS / ses / sh / group
    ff = trgdir.glob('**/*.jpg')
    for f in ff:
        if f.stem == imgname:
            return f.relative_to(settings.MEDIA_ROOT)


def parse_root_json(file):
    ses, imgname = file.stem.split('__')
    ses_yr, ses_name = ses.split('_')
    sh, cls, *_ = imgname.split('_')
    mo = group_dir.match(cls)
    if not mo: return
    yr = mo[1]
    gr = mo[2].lower().translate(en)
    if yr is None and sh == '90' and gr == 'd': yr = 2
    order = json.loads(file.read_text())
    if 'date' not in order:
        order['date'] = file_mtime(file)
    ordered = datetime.fromisoformat(order['date'])
    img = get_blank_img(ses, sh, cls, imgname)

    return {
        'ses': {'year': int(ses_yr), 'name': ses_name},
        'alb': {'sh': sh, 'year': int(yr), 'group': gr},
        'blk': {'imgname': imgname, 'ordered': ordered, 'order': order, 'img': img},
    }


class Command(BaseCommand):
    def handle(self, *args, **options):

        files = len(list((settings.MEDIA_ROOT / 'orders').glob('**/*.json')))
        print(f'json files count: {files}')
        done = 0

        data = []

        for f in ORDERS.iterdir():
            if f.is_file() and f.name.endswith('.json'):
                order = parse_root_json(f)
                if not order: continue
                data.append(order)
                done += 1

            elif f.is_dir() and '_' in f.name:
                ses_yr, ses_name = f.name.split('_')
                for SH in f.iterdir():
                    if not SH.is_dir() or not SH.name.isdigit(): continue
                    for CLS in SH.iterdir():
                        if not CLS.is_dir(): continue
                        mo = group_dir.match(CLS.name)
                        if not mo: continue
                        yr = mo[1]
                        gr = mo[2].lower().translate(en)
                        if yr is None and SH.name == '90' and gr == 'd': yr = 2
                        for file in CLS.glob('*.json'):
                            if not file.is_file(): continue
                            order = json.loads(file.read_text())
                            if 'date' not in order:
                                order['date'] = file_mtime(file)
                            ordered = datetime.fromisoformat(order['date'])
                            img = get_blank_img(f.name, SH.name, CLS.name, file.stem)
                            
                            o = {
                                'ses': {'year': int(ses_yr), 'name': ses_name},
                                'alb': {'sh': SH.name, 'year': int(yr), 'group': gr},
                                'blk': {'imgname': file.stem, 'ordered': ordered, 'order': order, 'img': img},
                            }
                            data.append(o)
                            done += 1


        return

        for SES in ORDERS.iterdir():
            if not SES.is_dir() or '_' not in SES.name: continue
            
            [ses_year, _, ses_name] = SES.name.partition('_')
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
                        group=mo[2].lower().translate(en) if mo[2] else "",
                        session=ses,
                    )

                    for file in CLS.iterdir():
                        if not file.is_file() or not file.name.endswith('.json'): continue
                        order = json.loads(file.read_text())
                        if 'date' not in order:
                            order['date'] = file_mtime(file)
                        ordered = datetime.fromisoformat(order['date'])

                        blank, is_new = Blank.objects.get_or_create(
                            album=alb,
                            imgname=file.stem,
                            defaults={
                                'ordered': ordered,
                                'order': order,
                                'img': None,
                            }
                        )

                        if is_new:
                            print(f'{SES.name}/{SH.name}/{CLS.name}/{file.name}')
                            done += 1

        print(f'found files: {files}, done: {done}')
