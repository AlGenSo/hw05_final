from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Group, Post, User
from ..constants import COUNT_POSTS_LIMIT_1, COUNT_POSTS_LIMIT_2


class StaticURLTests(TestCase):
    '''Класс для тестирования View'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Тестовая группа',
            slug='tests-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)
        self.user = User.objects.get(username='test_auth')
        self.author_client = Client()
        self.author_client.force_login(self.user)

        cache.clear()

    def test_pages_uses_correct_template(self):
        '''view-классы используют ожидаемые HTML-шаблоны'''
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                error = f'Ошибка: {reverse_name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error)

    def test_post_page_show_correct_context(self):
        '''В шаблон передан правильный контекст index'''
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        post_atr = {post.text: self.post.text,
                    post.id: self.post.id,
                    post.group: self.post.group,
                    post.author: self.post.author,
                    post.image: self.post.image}
        for value, expected in post_atr.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_list_page_show_correct_context(self):
        '''В шаблон передан правильный контекст group_list'''
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        post = response.context['page_obj'][0]
        group = response.context['group']
        post_atr = {post.text: self.post.text,
                    post.id: self.post.id,
                    post.group: self.post.group,
                    group: self.group,
                    post.author: self.post.author,
                    post.image: self.post.image}
        for value, expected in post_atr.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        '''В шаблон передан правильный контекст profile'''
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        post = response.context['page_obj'][0]
        author = response.context['author']
        post_atr = {post.text: self.post.text,
                    post.id: self.post.id,
                    post.group: self.post.group,
                    post.author: self.post.author,
                    post.image: self.post.image,
                    author: self.user}
        for value, expected in post_atr.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_detail_show_correct_context(self):
        '''В шаблон передан правильный контекст post_detail'''
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        post_atr = {post.text: self.post.text,
                    post.id: self.post.id,
                    post.group: self.post.group,
                    post.image: self.post.image,
                    post.author: self.post.author}
        for value, expected in post_atr.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_create_show_correct_context(self):
        '''В шаблон передан правильный контекст post_create'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_fields, expected)

    def test_post_edit_show_correct_context(self):
        '''В шаблон передан правильный контекст post_edit'''
        response = self.author_client.get(
            reverse('posts:edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_fields, expected)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertIsInstance(response.context.get('is_edit'), bool)

    def test_additional_verification_when_creating_a_post(self):
        '''Пост появляется на главной странице сайта,
        на странице выбранной группы, в профайле пользователя.'''
        project_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for address in project_pages:
            with self.subTest(adress=address):
                response = self.author_client.get(address)
                self.assertEqual(
                    response.context.get('page_obj')[0], self.post
                )

    def test_the_post_was_not_included_in_the_group(self):
        '''Если при создании поста указать группу,
        проверяем, что этот пост не попал в группу,
        для которой не был предназначен.'''
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                args=[self.another_group.slug]
            )
        )
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    '''Класс для тестирования пагинатора'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author_test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testos-slug',
            description='Тестовое описание',
        )
        heap_of_posts = []
        for i in range(COUNT_POSTS_LIMIT_1 + COUNT_POSTS_LIMIT_2):
            heap_of_posts.append(
                Post(
                    author=cls.user,
                    text=f'{i} тестовый текст',
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(heap_of_posts)

    def setUp(self):
        self.guest = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)
        self.user = User.objects.get(username='author_test')
        self.author_client = Client()
        self.author_client.force_login(self.user)

        cache.clear()

    def test_first_page_contains_ten_records(self):
        '''количество постов на первой странице
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_1
        )

    def test_second_page_contains_three_records(self):
        '''количество постов на второй странице
        равно количеству указанному в константе COUNT_POSTS_LIMIT_2
        в test/constants.py'''
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_2
        )

    def test_group_page_contains_three_records(self):
        '''количество постов на странице группы
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py'''
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_1
        )

    def test_group_page_contains_ten_records(self):
        '''количество постов на второй странице группы
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py'''
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2'
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_2
        )

    def test_profile_page_contains_three_records(self):
        '''количество постов на странице профиля
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py'''
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_1
        )

    def test_profile_page_contains_ten_records(self):
        '''количество постов на второй странице профиля
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py'''
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
            + '?page=2'
        )
        self.assertEqual(
            len(
                response.context['page_obj']
            ),
            COUNT_POSTS_LIMIT_2
        )
