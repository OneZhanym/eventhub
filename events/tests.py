from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Event


class EventSoftDeleteTests(TestCase):
	def setUp(self):
		self.owner = get_user_model().objects.create_user(username="event-owner")
		self.event = Event.objects.create(
			owner=self.owner,
			title="Test event",
			slug="test-event",
			summary="Test summary",
			description="Test description",
			starts_at="2026-10-09T12:00:00Z",
		)

	def test_soft_delete_updates_is_deleted(self):
		self.event.soft_delete()

		self.assertTrue(Event.objects.get(pk=self.event.pk).is_deleted)

	def test_post_soft_deletes_event_and_redirects(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse("events:event_delete", args=[self.event.pk])
		)

		self.assertRedirects(response, reverse("events:event_list"))
		self.assertTrue(Event.objects.get(pk=self.event.pk).is_deleted)

	def test_admin_can_soft_delete_any_event(self):
		admin = get_user_model().objects.create_superuser(
			username="delete-admin",
			email="delete-admin@example.com",
			password="test-password",
		)
		self.client.force_login(admin)
		detail_response = self.client.get(
			reverse("events:event_detail", args=[self.event.pk])
		)
		self.assertContains(
			detail_response,
			reverse("events:event_delete", args=[self.event.pk]),
		)

		response = self.client.post(
			reverse("events:event_delete", args=[self.event.pk])
		)

		self.assertRedirects(response, reverse("events:event_list"))
		self.assertTrue(Event.objects.get(pk=self.event.pk).is_deleted)

	def test_admin_can_update_any_event(self):
		admin = get_user_model().objects.create_superuser(
			username="site-admin",
			email="site-admin@example.com",
			password="test-password",
		)
		self.client.force_login(admin)
		detail_response = self.client.get(
			reverse("events:event_detail", args=[self.event.pk])
		)
		self.assertContains(
			detail_response,
			reverse("events:event_update", args=[self.event.pk]),
		)
		form_response = self.client.get(
			reverse("events:event_update", args=[self.event.pk])
		)
		self.assertContains(form_response, 'value="2026-10-09T12:00"')

		response = self.client.post(
			reverse("events:event_update", args=[self.event.pk]),
			{
				"title": "Updated event",
				"slug": "test-event",
				"summary": "Updated summary",
				"description": "Updated description",
				"starts_at": "2026-10-20T10:30",
				"is_published": "on",
			},
		)

		self.assertRedirects(response, reverse("events:event_list"))
		self.event.refresh_from_db()
		self.assertEqual(self.event.title, "Updated event")
		self.assertEqual(self.event.owner, self.owner)

	def test_non_admin_cannot_update_event(self):
		self.client.force_login(self.owner)
		detail_response = self.client.get(
			reverse("events:event_detail", args=[self.event.pk])
		)
		self.assertNotContains(
			detail_response,
			reverse("events:event_update", args=[self.event.pk]),
		)

		update_response = self.client.get(
			reverse("events:event_update", args=[self.event.pk])
		)
		self.assertEqual(update_response.status_code, 403)

	def test_non_owner_cannot_update_or_delete_event(self):
		other_user = get_user_model().objects.create_user(username="other-user")
		self.client.force_login(other_user)

		update_response = self.client.get(
			reverse("events:event_update", args=[self.event.pk])
		)
		delete_response = self.client.post(
			reverse("events:event_delete", args=[self.event.pk])
		)

		self.assertEqual(update_response.status_code, 403)
		self.assertEqual(delete_response.status_code, 404)
		self.event.refresh_from_db()
		self.assertFalse(self.event.is_deleted)

	def test_anonymous_user_is_redirected_to_login_to_edit(self):
		response = self.client.get(
			reverse("events:event_update", args=[self.event.pk])
		)

		self.assertRedirects(
			response,
			reverse("accounts:login") + "?next=" + reverse("events:event_update", args=[self.event.pk]),
		)

	def test_deleted_event_is_hidden_from_list_and_detail(self):
		self.event.soft_delete()

		list_response = self.client.get(reverse("events:event_list"))
		detail_response = self.client.get(
			reverse("events:event_detail", args=[self.event.pk])
		)

		self.assertNotContains(list_response, self.event.title)
		self.assertEqual(detail_response.status_code, 404)

	def test_authenticated_user_can_create_event_from_form(self):
		self.client.force_login(self.owner)
		home_response = self.client.get(reverse("events:home"))
		self.assertContains(home_response, reverse("events:event_create"))
		self.assertContains(home_response, self.owner.username)

		response = self.client.post(
			reverse("events:event_create"),
			{
				"title": "New event",
				"slug": "new-event",
				"summary": "A new event",
				"description": "Event description",
				"starts_at": "2026-10-20T10:30",
				"is_published": "on",
			},
		)

		self.assertRedirects(response, reverse("events:event_list"))
		created_event = Event.objects.get(slug="new-event")
		self.assertEqual(created_event.owner, self.owner)
