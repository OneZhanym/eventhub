from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Profile


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Электронная почта",
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        users = get_user_model().objects.filter(email__iexact=email)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if email and users.exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("avatar", "bio", "city", "birth_date")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "avatar": "Аватар",
            "bio": "О себе",
            "city": "Город",
            "birth_date": "Дата рождения",
        }
