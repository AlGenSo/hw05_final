from django import forms

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    '''Класс для формы создания поста'''

    class Meta:

        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа поста',
            'image': 'Загрузить изображение'
        }
        help_texts = {
            'text': 'Текст создаваемого поста',
            'group': 'Выбор группы для поста',
        }


class CommentForm(forms.ModelForm):
    '''Класс для создания поста'''

    class Meta:

        model = Comment
        fields = ('text',)
