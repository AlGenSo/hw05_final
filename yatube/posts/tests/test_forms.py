import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group, User
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
            content_type='image/gif'
        )
        form_post = {
            'text': 'Текст создаваемого поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_post, follow=True,
        )
        post = Post.objects.first()
        self.assertRedirects(
            response,
            reverse(
                ('posts:profile'),
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_post['text'])
        self.assertEqual(post.group.id, form_post['group'])
        self.assertEqual(post.author, self.user)

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
