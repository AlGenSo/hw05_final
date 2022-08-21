from django.urls import reverse
from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Post, Group, User


class StaticCacheTest(TestCase):
    '''Класс для тестирования кэша'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = User.objects.get(username='Author')
        self.author_client = Client()
        self.author_client.force_login(self.user)

        self.guest = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)

    def test_to_check_the_cache_operation(self):
        '''Проверка работы кэша'''
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        posts = response.content

        self.post.delete()

        response_outdated_cache = response
        outdated_posts = response_outdated_cache.content

        self.assertEqual(outdated_posts, posts)

        cache.clear()

        response = self.authorized_client.get(
            reverse('posts:index')
        )
        response_updated_cache = response
        updated_posts = response_updated_cache.content

        self.assertNotEqual(updated_posts, outdated_posts)
