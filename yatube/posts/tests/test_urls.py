from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    '''Класс для тестирования URL'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='ТЕстовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest = User.objects.create_user(username='user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)
        self.user = User.objects.get(username='auth')
        self.author_client = Client()
        self.author_client.force_login(self.user)

        cache.clear()

    def the_test_page_is_available_only_to_the_author(self):
        '''Страница доступна только автору'''
        response = self.author_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        '''Проверка доступности страниц
        и названия шаблонов приложения'''
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                if self.author_client:
                    response = self.author_client.get(adress)
                    self.assertTemplateUsed(response, template)

    def test_request_to_a_non_existent_page(self):
        '''Запрос к несуществующей странице вернёт ошибку 404.'''
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_availability_of_public_pages_for_guests(self):
        '''тест доступности публичных страниц для гостей'''
        templates_url_name = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]
        for adress in templates_url_name:
            with self.subTest(adress=adress):
                if self.client:
                    response = self.client.get(adress)
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.OK,
                    )

    def test_availability_of_private_pages_for_authorized_users(self):
        '''тесты доступности приватных страниц
        для авторизованных пользователей'''
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirect_anonymous_on_admin_login(self):
        '''тест, отражающий поведение,
        когда гость попадает на страницу редактирования поста'''
        response = self.client.get(f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_create_url_redirect_anonymous_on_admin_login(self):
        '''тест, отражающий поведение,
        когда гость попадает на страницу создания поста'''
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response,
            '/auth/login/?next=/create/'
        )

    def test_an_authorized_user_is_editing_not_his_post(self):
        '''тест, отражающий поведение,
        когда авторизованный пользователь
        пытается редактировать не свой пост.'''
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                ('posts:post_detail'),
                kwargs={'post_id': self.post.id}
            )
        )
