"""
    Custom template tag filters.
"""

import markdown
import re
from django import template
from django.utils.safestring import mark_safe, SafeData
from django.contrib.messages import constants as messages
from django.utils.html import conditional_escape
from django.template.defaultfilters import stringfilter
from django.utils.text import normalize_newlines

register = template.Library()


@register.filter(name='markdown2html')
def markdown2html(md_str):
    """
        Returns markdown string as HTML.
    """
    return mark_safe(markdown.markdown(md_str,  # nosec:B308:blacklist
                                       extensions=['markdown.extensions.fenced_code',
                                                   'markdown.extensions.nl2br']))


@register.filter(name='message_icon')
def message_icon(msg):
    """
        Returns the string class name of a message icon
        which feeds directly into Patternfly.
    """
    icons = {
        messages.ERROR: 'error-circle-o',
        messages.WARNING: 'warning-triangle-o',
        messages.SUCCESS: 'ok',
        messages.INFO: 'info',
    }
    return 'pficon-' + icons[msg.level]

@stringfilter
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&'+'nbsp;', esc(value)))
spacify.needs_autoescape = True
register.filter(spacify)

@register.filter(name='spacify_new')
@stringfilter
def spacify(value, autoescape=None):
    autoescape = autoescape and not isinstance(value, SafeData)
    value = normalize_newlines(value)
    if autoescape:
        value = escape(value)
    value = mark_safe(value.replace('  ', ' &nbsp;'))             
    return mark_safe(value.replace('\n', '<br />'))
