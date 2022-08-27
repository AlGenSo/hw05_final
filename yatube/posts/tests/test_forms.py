import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group, Comment, User
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormPostTests(TestCase):
    '''Класс для тестирования форм'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.form = PostForm
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_an_authorized_user_can_create_a_post(self):
        '''Валидная форма создает запись в Post
        авторизованным пользователем'''
        posts_count = Post.objects.count()
        posts_before = set(Post.objects.all())

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_post = {
            'text': 'Текст создаваемого поста',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_post, follow=True,
        )

        posts_after = set(Post.objects.all())
        posts_last = (posts_after - posts_before).pop()

        self.assertEqual(Post.objects.count() - posts_count, 1)

        self.assertRedirects(
            response,
            reverse(
                ('posts:profile'),
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(posts_last.text, form_post['text'])
        self.assertEqual(posts_last.group.id, form_post['group'])
        self.assertEqual(posts_last.image.name, 'posts/small.gif')
        self.assertEqual(posts_last.author, self.user)

    def test_an_authorized_user_can_edit_the_post(self):
        '''При отправке валидной формы авторизованным пользователем
        со страницы редактирования поста происходит изменение поста'''
        posts_count = Post.objects.count()
        form_post = {
            'text': 'Текст изменённого поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse(('posts:edit'), kwargs={'post_id': f'{self.post.id}'}),
            data=form_post,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                ('posts:post_detail'),
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                text=form_post['text'],
                group=self.group.id,
            ).exists()
        )


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
        self.guest = User.objects.create_user(username='user')
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

        comment_count = Comment.objects.count()
        comment_before = set(Comment.objects.all())

        comment_2 = Comment.objects.create(
            post=self.post,
            author=self.guest,
            text='себе свой совет посоветуй',
        )

        form_fields = {
            'author': self.guest,
            'text': comment_2.text,
            'post_id': comment_2.post.id,
        }
        response = self.author_client.get(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}
                    ),
            data=form_fields,
            follow=True
        )

        comment_count_add = Comment.objects.count()
        comment_after = set(Comment.objects.all())

        last_comment = (comment_after - comment_before).pop()

        self.assertEqual(Comment.objects.count() - comment_count, 1)

        self.assertRedirects(
            response,
            reverse(
                ('posts:post_detail'),
                kwargs={'post_id': self.post.id}
            )
        )

        self.assertEqual(
            comment_count_add,
            comment_count + 1,
        )

        self.assertEqual(last_comment.author, self.guest)
        self.assertEqual(last_comment.text, form_fields['text'])
        self.assertEqual(last_comment.post.id, form_fields['post_id'])

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
