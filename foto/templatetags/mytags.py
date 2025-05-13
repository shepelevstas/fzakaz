from django import template


register = template.Library()


@register.filter
def lookup(value, key):
  if not isinstance(value, dict):
    return None
  return value.get(key)


@register.filter
def rem_q(url, param):
  path, q = url.rsplit('?', 1)
  q = '&'.join(item for item in q.split('&') if item!=param)

  return '?'.join([path, q])


@register.simple_tag
def getlist(query_dict, key):
  return query_dict.getlist(key, [])



@register.filter
def rem_q_param(url, param):
  return {'url': url, 'param': param}


@register.filter
def rem_q_value(url_param, value):
  url = url_param['url']
  param = url_param['param'] + '=' + value

  return rem_q(url, param)


@register.filter
def add_q_param(url, param):
  return {'url': url, 'param': param}

@register.filter
def add_q_value(url_param, value):
  url = url_param['url']
  param = url_param['param']
  return f"{url}{'&' if '?' in url else '?'}{param}={value}"


@register.simple_tag
def set_q_param(url, param, value):
  return f'{url}{"&" if "?" in url else "?"}{param}={value}'

