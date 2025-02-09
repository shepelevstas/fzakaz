from django import template


register = template.Library()

@register.filter
def lookup(value, key):
  return value.get(key)
