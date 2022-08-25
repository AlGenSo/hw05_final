from django.contrib.auth.forms import UserCreationForm

from posts.models import User


class CreationForm(UserCreationForm):
    '''Класс для формы регистрации'''

    class Meta(UserCreationForm.Meta):
        '''Класс для настривания формы и переопределения параметров'''

        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
        )
