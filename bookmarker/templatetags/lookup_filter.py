from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
   return dictionary.get(key, '')
