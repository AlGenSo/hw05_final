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
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='user')

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
            author=cls.author,
            text='Тестовая пост',
            group=cls.group,
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

        cache.clear()

    def post_test_context(self, option, post, url):
        '''Проверка контекста поста'''
        response = self.authorized_client.get(url)
        if option:
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
                self.assertEqual(attr1, attr2)

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
        url = reverse('posts:index')
        return self.post_test_context(False, self.post, url)

    def test_group_list_page_show_correct_context(self):
        '''В шаблон передан правильный контекст group_list'''

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))

        group = response.context['group']

        self.assertEqual(group, self.group)

        url = reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'})

        return self.post_test_context(False, self.post, url)

    def test_profile_page_show_correct_context(self):
        '''В шаблон передан правильный контекст profile'''

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))

        author = response.context['author']
        following = response.context['following']

        post_context = {author: self.author,
                        following: True}
        for value, expected in post_context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

        url = reverse(
            'posts:profile',
            kwargs={'username': self.post.author})

        return self.post_test_context(False, self.post, url)

    def test_post_detail_show_correct_context(self):
        '''В шаблон передан правильный контекст post_detail'''

        commentic = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='себе свой совет посоветуй',
        )

        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))

        comments = response.context['comments'][0]
        self.assertEqual(comments, commentic)

        url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})

        return self.post_test_context(True, self.post, url)

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
            reverse('posts:profile', kwargs={'username': self.author}),
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
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testos-slug',
            description='Тестовое описание',
        )
        heap_of_posts = []
        for i in range(COUNT_POSTS_LIMIT_1 + COUNT_POSTS_LIMIT_2):
            heap_of_posts.append(
                Post(
                    author=cls.author,
                    text=f'{i} тестовый текст',
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(heap_of_posts)

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.author)

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
                reverse('posts:profile', kwargs={'username': self.author})
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
                reverse('posts:profile', kwargs={'username': self.author})
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
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_to_check_the_cache_operation(self):
        '''Проверка работы кэша'''
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        posts = response.content

        self.post.delete()

        response = self.authorized_client.get(
            reverse('posts:index')
        )
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

        Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).delete()

        count_follows = Follow.objects.count()

        self.assertEqual(count_follows, 0)

        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            )
        )

        self.assertEqual(Follow.objects.count(), count_follows + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_a_new_post_in_the_subscribers_feed(self):
        '''Новая запись пользователя
        появляется в ленте тех, кто на него подписан'''
        response = self.authorized_client.get(
            reverse(
                'posts:follow_index',
            )
        )

        self.assertEqual(
            self.post,
            response.context['page_obj'].object_list[0],
        )

    def test_the_new_entry_is_not_displayed_in_the_feed_of_the_unsigned(self):
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

        self.assertEqual(Follow.objects.count(), 1)

        response = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertRedirects(
            response,
            reverse(
                ('posts:profile'),
                kwargs={'username': self.author}
            )
        )
