from django import template
from django.utils.safestring import mark_safe
import markdown


register = template.Library()


@register.filter
def markdownify(text):
    return mark_safe(markdown.markdown(text, safe_mode='escape'))


@register.filter
def markdownify_title(text):
    """Same as markdownify but removes the paragraph tags."""
    output = markdown.markdown(text, safe_mode='escape')
    if output.startswith('<p>') and output.endswith('</p>'):
        output = output[3:-4]
    return mark_safe(output)