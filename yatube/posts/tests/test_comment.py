from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, Comment, User


class StaticCommentTest(TestCase):
    '''Класс для тестирования комментариев'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='commentator')
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='не читал, но осуждаю!',
        )

    def setUp(self):
        self.guest = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)

        self.user = User.objects.get(username='commentator')
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_comment_add_authorized_client(self):
        '''для авторизованного пользователя:
           комментарий появляется на странице поста
           пользователь перенаправляется обратно на страницу posts:post_detail.
           Проверка корректности полей формы.
        '''
        form_fields = {
            'author': self.user,
            'text': self.comment.text,
            'post_id': self.post.id,
        }
        response = self.author_client.get(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}
                    ),
            data=form_fields,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                ('posts:post_detail'),
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                author=self.user,
                text=self.comment.text,
                post_id=self.post.id,
            ).exists()
        )

    def test_adding_an_unauthorized_users_comment(self):
        '''для не авторизованного пользователя:
           Перенаправление на страницу авторизации
           при попытке оставить коммент.
        '''
        response = self.client.get(
            f'/posts/{self.post.id}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
