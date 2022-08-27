from django import template

from posts.constants import CACHE_UPDATE

register = template.Library()


@register.simple_tag
def cache_updates():
    '''Переменная для времени кэширования'''
    return {'cache_updates': CACHE_UPDATE}
