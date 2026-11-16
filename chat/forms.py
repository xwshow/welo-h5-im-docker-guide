from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """Minimal signup: account + password only. No invite / referrer field."""

    username = forms.CharField(
        label="账号",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "请输入账号",
                "autocomplete": "username",
                "autocapitalize": "off",
            }
        ),
    )
    password1 = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "至少 8 位",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="确认密码",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "再次输入密码",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Drop Django's long English help texts for a cleaner mobile form.
        for name in ("username", "password1", "password2"):
            self.fields[name].help_text = ""


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="账号",
        widget=forms.TextInput(
            attrs={
                "placeholder": "请输入账号",
                "autocomplete": "username",
                "autocapitalize": "off",
            }
        ),
    )
    password = forms.CharField(
        label="密码",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "请输入密码",
                "autocomplete": "current-password",
            }
        ),
    )


class AddFriendForm(forms.Form):
    username = forms.CharField(
        label="对方账号",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "输入对方账号"}),
    )
