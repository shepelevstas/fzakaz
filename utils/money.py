# conding=utf-8


PRICES_23_24 = {
  "f10":     350,
  "f15":     350,
  "f20":     400,
  "f30":     500,
  "m10":     350,
  "m15":     400,
  "calend":  500,
  "rasp":    500,
  "pill":   1000,
  "mug":     700,
  "tshirt": 1000,
  "tsize":     0,
  "book":   1300,
  "set":    1000,
}

PRICES = PRICES_23_24


def order_cost(order_dict, pricelist=PRICES):
  cost = 0

  for k, v in order_dict.items():
    if not v or not isinstance(v, (int, str)):continue
    if '_' not in k:continue
    col, row = k.split('_')
    price = pricelist.get(row, 0)
    if row in ('tsize',):continue
    if col in ('port', 'vint', 'coll', 'all'):
      cost += price * int(v)

  return cost
