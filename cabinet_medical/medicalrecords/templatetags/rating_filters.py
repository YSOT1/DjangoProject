from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def filter_rating(ratings, rating_value):
    """Filter ratings by rating value"""
    return [r for r in ratings if r.rating == rating_value]

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 