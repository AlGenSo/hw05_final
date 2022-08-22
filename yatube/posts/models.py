from django.db import models
from django.contrib.auth import get_user_model

from .constants import STRING_LENGHT_LIMIT

User = get_user_model()


class Post(models.Model):
    '''Объявляем класс Post, наследник класса Model из пакета models
    Описываем поля модели и их типы'''

    text = models.TextField(
        verbose_name='Текст публикации',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        'Group',
        verbose_name='Сообщество',
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:

        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.text[:STRING_LENGHT_LIMIT]


class Group(models.Model):
    '''Объявляем класс Group, наследник класса Model из пакета models
    Описываем поля модели и их типы'''

    title = models.CharField(
        verbose_name='Сообщество',
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name='URL - адрес',
        unique=True,
    )
    description = models.TextField(
        verbose_name='Описание',
    )

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    '''Класс Коммент, для создания комментариев к постам.
    Описываем поля модели'''
    post = models.ForeignKey(
        Post,
        verbose_name="Комментарий",
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст комментария',
    )
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    '''Класс подписки на авторов'''
    user = models.ForeignKey(
        User,
        verbose_name='Подписота',
        related_name='follower',
        on_delete=None,
    )

    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        related_name='following',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"подписчик: '{self.user}', автор: '{self.author}'"
