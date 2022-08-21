from django import forms


def validate_not_empty(value):
    if value == '':
        raise forms.ValidationError(
            'Ошибка! Не заполнено поле!',
            params={'value': value},
        )
