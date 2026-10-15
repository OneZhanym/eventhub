from django.test import TestCase
from django.urls import reverse
from .models import Event


class EventSoftDeleteTests(TestCase):
	def setUp(self):
		self.event = Event.objects.create(
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
		response = self.client.post(
			reverse("events:event_delete", args=[self.event.pk])
		)

		self.assertRedirects(response, reverse("events:event_list"))
		self.assertTrue(Event.objects.get(pk=self.event.pk).is_deleted)

	def test_deleted_event_is_hidden_from_list_and_detail(self):
		self.event.soft_delete()

		list_response = self.client.get(reverse("events:event_list"))
		detail_response = self.client.get(
			reverse("events:event_detail", args=[self.event.pk])
		)

		self.assertNotContains(list_response, self.event.title)
		self.assertEqual(detail_response.status_code, 404)
