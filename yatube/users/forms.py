from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


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
