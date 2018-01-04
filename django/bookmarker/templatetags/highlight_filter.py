import re

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def highlight_term(text, term):
    if term.lower() in text.lower():
        text = re.sub(
            '(' + term + ')',
            r'<span class="highlight">\1</span>',
            text,
            flags=re.I
        )

    return mark_safe(text)
