import json
from datetime import datetime
# from sortedcontainers import SortedList

from django.core.signing import Signer, BadSignature
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import F, Q, BooleanField, ExpressionWrapper

from foto.forms import UploadBlanksForm, ContactInfoForm

from .utils import en
from .models import Album, Session, Blank, Pricelist


signer = Signer()


class Sorted:
    def __init__(self, key, reverse=False, attrs=None, add=None, item=None):
        self.__dict__['_dict'] = {}
        self.__dict__['_key'] = key
        self.__dict__['_rev'] = reverse
        self.__dict__['_attrs'] = attrs or {}
        self.__dict__['_add_fn'] = add
        self.__dict__['item'] = item

    def __getattr__(self, name):
        return self._attrs.get(name)

    def __setattr__(self, name, value):
        self._attrs[name] = value

    def add(self, key, item):
        self._dict[key] = item

    def get_add(self, key, add=None):
        if key in self._dict: return self._dict[key]
        if self._add_fn:
            item = self._add_fn(add)
            self._dict[key] = item
        return self._dict.get(key)

    def get(self, key, fn=None):
        if fn is None:
            return self._dict.get(key)
        if key not in self._dict:
            new_item = fn()
            self._dict[key] = new_item
        return self._dict[key]

    def items(self):
        return sorted(self._dict.values(), key=self._key, reverse=self._rev)


def index(req):

    if req.method == "POST" and req.POST.get('action'):
        action = req.POST.get('action')

        if action == 'close':
            Album.objects.get(id=req.POST.get('album_id')).close()
        elif action == 'close_all':
            Session.objects.get(id=req.POST.get('session_id')).close_all(req.POST.get('album_sh'))
        elif action == 'open':
            Album.objects.get(id=req.POST.get('album_id')).open()
        elif action == 'open_all':
            Session.objects.get(id=req.POST.get('session_id')).open_all(req.POST.get('album_sh'))
        elif action == 'upload':
            res, blank_or_form = upload(req)
            if not res:
                print(blank_or_form)
            return JsonResponse({
                'success': res,
                'form': blank_or_form.errors if blank_or_form is UploadBlanksForm else None,
            })
        elif action == 'add_session':
            pass

        # match req.POST.get('action'):
        #     case 'close':
        #         Album.objects.get(id=req.POST.get('album_id')).close()
        #     case 'close_all':
        #         Session.objects.get(id=req.POST.get('session_id')).close_all(req.POST.get('album_sh'))
        #     case 'open':
        #         Album.objects.get(id=req.POST.get('album_id')).open()
        #     case 'open_all':
        #         Session.objects.get(id=req.POST.get('session_id')).open_all(req.POST.get('album_sh'))
        #     case 'upload':
        #         res, blank_or_form = upload(req)
        #         if not res:
        #             print(blank_or_form)
        #         return JsonResponse({
        #             'success': res,
        #             'form': blank_or_form.errors if blank_or_form is UploadBlanksForm else None,
        #         })
        #     case 'add_session':
        #         pass

    albums = Album.objects.all()

    ses = req.GET.get('ses')
    sh = req.GET.get('sh')

    if ses:
        [yr, _, nm] = ses.partition('_')
        ses = Session.objects.get(year=yr, name=nm)
        albums = albums.filter(session=ses)

    if sh:
        albums = albums.filter(sh=sh)

    sessions = Sorted( # sorted sessoins
        key=lambda ses: (ses.item.year, ses.item.created),
        reverse=True,
        add=lambda alb: Sorted( # sorted sh
            key=lambda sh: sh.name,
            item=alb.session,
            attrs={'ordered': 0, 'blanks': 0},
            add=lambda alb: Sorted( # sorted albums
                key=lambda alb: (alb.year, alb.group),
                attrs={'name': alb.sh, 'ordered': 0, 'blanks': 0},
            )
        )
    )
    for alb in albums:
        alb.cache_progress()
        ses = sessions.get_add(alb.session_id, add=alb)
        ses.ordered += alb.ordered
        ses.blanks += alb.blanks
        sh = ses.get_add(alb.sh, add=alb)
        sh.ordered += alb.ordered
        sh.blanks += alb.blanks
        sh.add(alb.id, alb)

    return render(req, 'zakaz/index.html', {
        'albums': albums,
        'edit': True,
        'sessions': sessions,
        'form': UploadBlanksForm(old=False),
    })


def album(req, sign):

    return render(req, 'zakaz/album.html', {
        'album': Album.from_sign(sign),
        'sign': sign,
    })


def upload(req):
    form = UploadBlanksForm(req.POST, req.FILES, old=False)

    if form.is_valid():
        print('[VALID]')
        data = form.cleaned_data
        ses_id = data['session']
        sh = data['sh']
        yr = data['yr']
        gr = data['gr'].lower().translate(en)

        ses = Session.objects.get(id=ses_id)

        album, created = Album.objects.get_or_create(
            session=ses,
            sh=sh,
            year=yr,
            group=gr,
        )

        blank = None

        for file in req.FILES.getlist('files'):
            print('[BLANK]')
            blank = Blank.objects.create(
                album=album,
                imgname=file.name.rsplit('.', 1)[0],
                img=file,
            )

        return blank is not None, blank
    print('[WRONG]')
    return False, form


def blank(req, sign):

    try:
        unsigned = signer.unsign(sign)
    except BadSignature:
        return HttpResponse('NotFound', 404)

    isodate = req.GET.get('isodate')

    [_, id] = unsigned.rsplit('__', 1)
    blank = Blank.objects.select_related('album__session__pricelist').get(id=id)
    blank.is_closed = blank.album.is_closed

    if isodate:
        order = next((i for i in blank.orders if i['date'] == isodate), None)
        if order:
            blank.ordered = datetime.fromisoformat(order['date'])
            blank.order = order
            blank.is_closed = True
            blank.is_cancelable = -100 < order['status'] < 200

    contacts = ContactInfoForm(req.POST or blank.order or None, initial={'name': blank.name})

    order = None
    if req.method == "POST":
        order = dict(i for i in req.POST.items() if i[0] not in ('csrfmiddlewaretoken', 'action') and i[1] and i[1] != '0')

        if contacts.is_valid():
            action = req.POST.get('action')
            message = ''

            if action == 'save':
                blank.ordered = datetime.now()
                order['date'] = blank.ordered.replace(microsecond=0).isoformat()
                blank.order = order
                if blank.name and order['name'].strip() and blank.name != order['name'].strip():
                    blank.name = order['name'].strip()
                message = 'Спасибо за заказ! Пока прием заказов не закрыт, Вы всегда можете вернуться и изменить его! Это не создаст новый заказ, а изменит имеющийся! Если Вам полагается электронный портрет в подарок - не забудьте указать правильный адрес электронной почты. Можно вернуться назад и изменить контактные данные.'

            elif action == 'cancel_order':
                blank.cancel(isodate)
                message = 'Заказ отменен!'

            blank.save()
            return render(req, 'zakaz/message.html', {
                'message': message,
            })

    return render(req, 'zakaz/blank.html', {
      'blank': blank,
      'contacts': contacts,
    })


def pricelists(req):

    if req.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'data': [p.as_json() for p in Pricelist.objects.all()]
        })

    if req.method == "POST":
        data = json.loads(req.body.decode('utf8'))
        id = data.get('id')
        if id and id.isdigit():
            pricelist = Pricelist.objects.get(id=id)
        else:
            pricelist = Pricelist()
        pricelist.name = data['name']
        pricelist.formats = list(data['formats'].values())
        pricelist.themes = data['themes']
        pricelist.bonus = data['bonus']
        pricelist.save()

        return JsonResponse({'success': True, 'id': pricelist.id})

    return render(req, 'zakaz/pricelists.html', {})


def table(req, sign):
    album = Album.from_sign(sign)

    blanks = album.blank_set.all()

    if req.method == "POST":
        if req.POST.get('action') == 'load_csv':
            file = req.FILES.get('file')
            for line in file:
                line = line.strip().decode(encoding='cp1251').split(';')
                if len(line) < 2: continue
                [imgn, name, *rest] = line
                if len(imgn) != 4 or not imgn.isdigit(): continue
                blank = blanks.filter(imgname__contains=imgn)
                if not blank.exists(): continue
                blank = blank[0]
                blank.name = name
                blank.save()

        if req.POST.get('action') == 'update_blank':
            file = req.FILES.get('blank')
            blank_id = req.POST.get('id')
            blank = Blank.objects.get(id=blank_id)
            blank.img.delete()
            blank.img = file
            blank.save()

    for b in blanks:
        if not b.name:
            b.name = b.order['name'] if b.order and 'name' in b.order else next((o['name'] for o in b.orders if 'name' in o), '--')
        for o in b.orders:
            if 'date' not in o:continue
            o['date'] = datetime.fromisoformat(o['date'])


    return render(req, 'zakaz/table.html', {
       'album': album,
       'blanks': blanks,
    })
