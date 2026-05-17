en = str.maketrans(
  'абвгдежзиклмнопрстуфхцчшщэюя',
  'abvgdejziklmnoprstyfxCcwWquY',
)

translit = str.maketrans(
  'фотхмагнипдушкржблв еёзсчцщюыъьэяй',
  "fotxmagnipdyskrjblv_eezs4csui''qji"
)

class Sorted:
    def __init__(self, key, items=None, **kw):
        self.key = key
        self.items = items
        self.kw = kw

    def data(self, data, lvl=1):
        fst = None
        cache = {}
        keys = set()
        for i in data:
            fst = fst or i
            k = self.key(i)
            ctx = cache.setdefault(id(i), {})
            ctx[lvl] = {'key': k}
            keys.add(k)

        for k in sorted(keys):
            ii = sorted((a for a in data if k==cache[id(a)][lvl]['key']))
            if self.items:
                s = self.items.data(ii, lvl+1)
                for k,f in self.kw.items():
                    setattr(s, k, f(fst))
                yield s
            else:
                yield ii

        


s = Sorted(
    key=lambda i: (i.session.year, i.session.created),
    name=lambda i: i.session.name,
    ordered=lambda items: sum(a.ordered for a in items),
    items=Sorted(
        key=lambda i: i.sh,
        ordered=lambda ii: sum(a.ordered for a in ii),
        items=Sorted(
            key=lambda i: (i.year, i.group),
            name=lambda i: f'{i.year}{i.group}',
            ordered=lambda ii: sum(a.ordered for a in ii),
        ),
    ),
)
