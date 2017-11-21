from django import template
from django.utils.html import mark_safe

# Admin view descriptions
register = template.Library()


@register.simple_tag()
def model_desc(obj):
    if obj.__doc__:
        return mark_safe('<p>{}</p>'.format(obj.__doc__))
    return ''
