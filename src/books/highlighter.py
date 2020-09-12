import re

from django.template.defaultfilters import truncatechars, truncatechars_html


def highlight(text, query, truncate_to=None):
    """Replaces all instances of [query] within [text] with <highlight>[query]</highlight, and truncates to the first [num_chars] characters (respecting html)."""
    query_lower = query.lower()
    text_lower = text.lower()
    if query_lower in text_lower:
        r = '({})'.format(re.escape(query))
        s = re.sub(r, r'<mark>\1</mark>', text, flags=re.IGNORECASE)

        if truncate_to:
            # Make sure the query appears in the truncated result.
            if query_lower in text_lower[:truncate_to]:
                return truncatechars_html(s, truncate_to)
            else:
                i = text_lower.index(query_lower) - (truncate_to // 2)
                return '…' + truncatechars_html(s[i:], truncate_to)
        else:
            return s
    else:
        if truncate_to:
            return truncatechars(text, truncate_to)
        else:
            return text