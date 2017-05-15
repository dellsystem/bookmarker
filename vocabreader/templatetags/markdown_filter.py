from django import template
from django.utils.safestring import mark_safe
import markdown


register = template.Library()


@register.filter
def markdownify(text):
    return mark_safe(markdown.markdown(text, safe_mode='escape') )
