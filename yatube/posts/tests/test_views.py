from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Group, Post, Follow, Comment, User
from ..constants import COUNT_POSTS_LIMIT_1, COUNT_POSTS_LIMIT_2


class StaticURLTests(TestCase):
    '''Класс для тестирования View'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_auth')
        cls.guest = User.objects.create_user(username='HasNoName')

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
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.guest,
        )

    def setUp(self):
        self.guest = User.objects.get(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)

        self.user = User.objects.get(username='test_auth')
        self.author_client = Client()
        self.author_client.force_login(self.user)

        cache.clear()

    def post_test_context(self, response, post, url):

        response = response.get(url)
        if url == reverse(
            'posts:post_detail',
                kwargs={'post_id': self.post.id}):
            post_in_response = response.context['post']
        else:
            post_in_response = response.context['page_obj'][0]

        post_attr = {
            post.text: post_in_response.text,
            post.id: post_in_response.id,
            post.group: post_in_response.group,
            post.author: post_in_response.author,
            post.image: post_in_response.image
        }

        for attr1, attr2 in post_attr.items():
            with self.subTest(attr1=attr1):
                self.assertAlmostEqual(attr1, attr2)

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
        response = self.authorized_client
        url = reverse('posts:index')
        post = self.post
        return self.post_test_context(response, post, url)

    def test_group_list_page_show_correct_context(self):
        '''В шаблон передан правильный контекст group_list'''

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))

        post = response.context['page_obj'][0]
        group = response.context['group']

        self.assertEqual(group, self.group)

        response = self.authorized_client
        url = reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'})
        post = self.post

        return self.post_test_context(response, post, url)

    def test_profile_page_show_correct_context(self):
        '''В шаблон передан правильный контекст profile'''

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))

        post = response.context['page_obj'][0]
        author = response.context['author']
        following = response.context['following']

        post_atr = {author: self.user,
                    following: True}
        for value, expected in post_atr.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

        response = self.authorized_client
        url = reverse(
            'posts:profile',
            kwargs={'username': self.post.author})
        post = self.post

        return self.post_test_context(response, post, url)

    def test_post_detail_show_correct_context(self):
        '''В шаблон передан правильный контекст post_detail'''

        commentic = Comment.objects.create(
            post=self.post,
            author=self.guest,
            text='себе свой совет посоветуй',
        )

        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        post = response.context['post']
        comments = response.context['comments'][0]
        self.assertEqual(comments, commentic)

        response = self.authorized_client
        url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        post = self.post

        return self.post_test_context(response, post, url)

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

    def test_pages_contains_ten_records(self):
        '''
        количество постов:
        на первой странице,
        на странице группы
        на странице профиля
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py
        '''
        template_response = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': self.user})
            ),
        ]

        for resp in template_response:
            with self.subTest(resp=resp):
                if self.authorized_client:
                    response = resp
                    self.assertEqual(
                        len(
                            response.context['page_obj']
                        ),
                        COUNT_POSTS_LIMIT_1,
                    )

    def test_pages_contains_tree_records(self):
        '''
        количество постов:
        на второй странице,
        на второй странице группы,
        на второй странице профиля
        равно количеству указанному в константе COUNT_POSTS_LIMIT_1
        в test/constants.py
        '''
        template_response = [
            self.client.get(reverse('posts:index') + '?page=2'),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
                + '?page=2'
            ),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': self.user})
                + '?page=2'
            )
        ]

        for resp in template_response:
            with self.subTest(resp=resp):
                if self.authorized_client:
                    response = resp
                    self.assertEqual(
                        len(
                            response.context['page_obj']
                        ),
                        COUNT_POSTS_LIMIT_2,
                    )


class StaticCacheTest(TestCase):
    '''Класс для тестирования кэша'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='User')
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
        self.author = User.objects.get(username='Author')
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.user = User.objects.get(username='User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_to_check_the_cache_operation(self):
        '''Проверка работы кэша'''
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        posts = response.content

        self.post.delete()

        outdated_posts = response.content

        self.assertEqual(outdated_posts, posts)

        cache.clear()

        response = self.authorized_client.get(
            reverse('posts:index')
        )
        updated_posts = response.content

        self.assertNotEqual(updated_posts, outdated_posts)


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

    def test_no_subscription_subscription_subscribed(self):
        '''Авторизованный пользователь не подпсан,
        подписывается,
        подписка появляется'''

        self.follow = Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).delete()

        response = self.authorized_client.get(
            reverse(
                'posts:follow_index',
            )
        )

        self.assertNotContains(response, self.follow)

        follow_test = Follow.objects.create(
            author=self.author,
            user=self.user,
        )

        self.assertContains(response, follow_test.author)

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
            Post.objects.filter(
                author=self.author,
                group=self.group,
                text=self.post.text,
            )
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

    def test_unsubscribe(self):
        '''тест отписки'''
        response = self.authorized_client.get(
            f'/profile/{self.author}/unfollow',
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                ('posts:profile'),
                kwargs={'username': self.author}
            )
        )
