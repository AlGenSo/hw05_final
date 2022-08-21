from django.core.paginator import Paginator

from .constants import LIMIT_COUNTS_POSTS


def pagination(posts, request):
    paginator = Paginator(posts, LIMIT_COUNTS_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
