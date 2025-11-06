from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """Replaces underscores or any substring: 'old:new'"""
    try:
        old, new = arg.split(':', 1)
        return value.replace(old, new)
    except ValueError:
        return value