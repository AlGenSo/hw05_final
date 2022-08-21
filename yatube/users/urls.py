from django.contrib.auth.views import (
    LogoutView,
    LoginView,
    PasswordResetView,
    PasswordChangeView,
)
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = 'users'

urlpatterns = [
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup',
    ),
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout',
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login',
    ),
    path(
        'password_change/',
        PasswordChangeView.as_view(
            template_name='users/password/password_change_form.html',
        ),
        name='password_change',
    ),
    path(
        'password_change/done/',
        PasswordChangeView.as_view(
            template_name='users/password/password_change_done.html',
        ),
        name='password_change_done',
    ),
    path(
        'password_reset/',
        PasswordResetView.as_view(
            template_name='users/password/password_reset_form.html'
        ),
        name='password_reset_form',
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/token/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/passsword/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
]
