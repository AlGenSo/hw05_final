from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    '''Класс для обработки страницы Об авторе'''

    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    '''Класс для обработки страницы Технологии'''

    template_name = 'about/tech.html'
