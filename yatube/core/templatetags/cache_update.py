from atexit import register
from posts.constants import CACHE_UPDATE

from django import template

register = template.Library()


@register.simple_tag
def cache_updates():
    '''Переменная для времени кэширования'''
    return {'cache_updates': CACHE_UPDATE}
