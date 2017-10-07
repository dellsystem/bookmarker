import re

from django import template
from django.utils.safestring import mark_safe
import markdown


register = template.Library()


@register.filter
def markdownify(text):
    return mark_safe(
        markdown.markdown(
            text,
            ['superscript'],
            safe_mode='escape',
            smart_emphasis=False
        ).replace('    ', '&ensp;')
    )


OL_REGEX = re.compile('([0-9]+)\. ')
@register.filter
def markdownify_title(text):
    """Same as markdownify but removes the paragraph and header tags, and
    prevents ordered lists from being created."""
    if OL_REGEX.match(text):
        text = OL_REGEX.sub(r'\1\\. ', text)
    output = markdown.markdown(text, safe_mode='escape', smart_emphasis=False)
    if output.startswith('<p>') and output.endswith('</p>'):
        output = output[3:-4]
    if output.startswith('<h1>') and output.endswith('</h1>'):
        output = output[4:-5]
    return mark_safe(output)
