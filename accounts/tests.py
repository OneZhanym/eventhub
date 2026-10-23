from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image

from .forms import UserUpdateForm
from .models import Profile


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile-user",
            email="profile@example.com",
            password="Test-password-539!",
        )

    def test_signup_creates_profile(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new-user",
                "email": "new@example.com",
                "password1": "Test-password-539!",
                "password2": "Test-password-539!",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(
            Profile.objects.filter(user__username="new-user").exists()
        )

    def test_user_creation_signal_creates_profile(self):
        user = get_user_model().objects.create_user(
            username="signal-user",
            password="Test-password-539!",
        )

        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_page_is_available_to_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile-user")
        self.assertContains(response, "Дата регистрации")
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_pages_require_authentication(self):
        for url_name in ("accounts:profile", "accounts:profile_edit"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(
                    response,
                    f"{reverse('accounts:login')}?next={reverse(url_name)}",
                )

    def test_user_can_update_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Алия",
                "last_name": "Иванова",
                "email": "aliya@example.com",
                "bio": "Люблю городские события.",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Алия")
        self.assertEqual(self.user.last_name, "Иванова")
        self.assertEqual(self.user.email, "aliya@example.com")
        self.assertEqual(self.user.profile.bio, "Люблю городские события.")

    def test_profile_edit_form_renders_file_and_date_fields(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile_edit"))

        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'type="file"')
        self.assertContains(response, 'type="date"')
        self.assertNotContains(response, 'name="username"')

    def test_user_can_upload_profile_avatar(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), color="red").save(image_buffer, format="PNG")
        self.client.force_login(self.user)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("accounts:profile_edit"),
                    {
                        "first_name": "",
                        "last_name": "",
                        "email": self.user.email,
                        "bio": "",
                        "city": "",
                        "birth_date": "",
                        "avatar": SimpleUploadedFile(
                            "avatar.png",
                            image_buffer.getvalue(),
                            content_type="image/png",
                        ),
                    },
                    follow=True,
                )

                self.assertContains(response, "Профиль обновлён")
                self.user.profile.refresh_from_db()
                self.assertTrue(self.user.profile.avatar)
                self.assertTrue(self.user.profile.avatar.storage.exists(
                    self.user.profile.avatar.name
                ))

    def test_profile_update_rejects_another_users_email(self):
        get_user_model().objects.create_user(
            username="other-user",
            email="taken@example.com",
            password="Test-password-539!",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "",
                "last_name": "",
                "email": "taken@example.com",
                "bio": "",
                "city": "",
                "birth_date": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пользователь с таким email уже существует.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile@example.com")

    def test_profile_page_lists_only_non_deleted_user_events(self):
        from events.models import Event

        active = Event.objects.create(
            owner=self.user,
            title="Моё событие",
            slug="my-profile-event",
            summary="Событие из профиля",
            description="Описание",
            starts_at="2026-10-20T10:30:00Z",
        )
        deleted = Event.objects.create(
            owner=self.user,
            title="Удалённое событие",
            slug="deleted-profile-event",
            summary="Скрытое событие",
            description="Описание",
            starts_at="2026-10-20T10:30:00Z",
            is_deleted=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertContains(
            response,
            reverse("events:event_detail", args=[active.pk]),
        )
        self.assertNotContains(response, deleted.title)

    def test_user_update_form_rejects_another_users_email(self):
        get_user_model().objects.create_user(
            username="another-user",
            email="taken@example.com",
            password="Test-password-539!",
        )

        form = UserUpdateForm(
            data={
                "first_name": "",
                "last_name": "",
                "email": "taken@example.com",
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
