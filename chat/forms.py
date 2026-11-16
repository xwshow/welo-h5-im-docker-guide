from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="账号")
    password = forms.CharField(label="密码", widget=forms.PasswordInput)


class AddFriendForm(forms.Form):
    username = forms.CharField(label="对方账号", max_length=150)
