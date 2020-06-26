import io

from django.test import TestCase
from django.urls import reverse


class IdentityFormTestCase(TestCase):
    def setUp(self):
        self.index_url = reverse('index')

    def test_index_page(self):
        resp = self.client.get(self.index_url)
        self.assertEqual(resp.status_code, 200)

    def test_empty_form_submition(self):
        resp = self.client.post(self.index_url, data={})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.count(b'class="errorlist"'), 4)
        self.assertIn(b'This field is required.', resp.content)

    def test_text_field_form_submition(self):
        data = {
            "name": "Vardenis",
            "surname": "Pavardenis",
            "birth_date": "2020-01-01",
        }

        resp = self.client.post(self.index_url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.count(b'class="errorlist"'), 1)
        self.assertIn(b'This field is required.', resp.content)

    def test_successful_form_submition(self):
        data = {
            "name": "Vardenis",
            "surname": "Pavardenis",
            "birth_date": "2020-01-01",
            "document_picture": io.BytesIO(b'test_file_content'),
        }

        resp = self.client.post(self.index_url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'You have entered correct information!', resp.content)
        self.assertNotIn(b'class="errorlist"', resp.content)
        self.assertNotIn(b'This field is required.', resp.content)
