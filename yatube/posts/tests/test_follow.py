from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client

from ..models import Post, Group, Follow, User


class StaticFollowTest(TestCase):
    '''Класс тестирования подписок'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='follower')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )

        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user,
        )

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.followers = self.user.follower.count()

    def test_subscription_of_an_unauthorized_user(self):
        '''для не авторизованного пользователя:
           Перенаправление на страницу авторизации
           при попытке подписаться.
        '''
        response = self.client.get(
            f'/profile/{self.author}/follow/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/profile/{self.follow.author}/follow/'
        )

    def test_the_author_cannot_subscribe_to_himself(self):
        '''автор не может подписаться на самого себя'''

        response = self.author_client.get(
            'posts:profile_follow',
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_An_authorized_user_can_subscribe_to_other_users(self):
        '''Авторизованный пользователь
        может подписываться на других пользователей'''

        response = self.authorized_client.get(
            reverse(
                'posts:follow_index',
            )
        )
        self.assertContains(response, self.follow.author)

    def test_A_new_user_record_appears_in_the_subscribers(self):
        '''Новая запись пользователя
        появляется в ленте тех, кто на него подписан'''
        response = self.authorized_client.get(
            reverse(
                'posts:follow_index',
            )
        )
        self.assertIn(
            response.context['page_obj'].object_list[0],
            Post.objects.all()
        )

    def test_The_new_entry_does_not_appear_in_the_unsigned_feed(self):
        '''Новая запись пользователя
        не появляется в ленте тех, кто на него подписан'''
        Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).delete()
        response = self.authorized_client.get(
            reverse(
                'posts:follow_index',
            )
        )
        self.assertNotIn(self.post,
                         response.context['page_obj'])
