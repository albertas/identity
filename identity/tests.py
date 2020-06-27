import io
import json
from unittest import mock

from django.test import TestCase
from django.urls import reverse


class ResponseMock:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def json(self):
        return json.loads(self.content)


class IdentityFormTestCase(TestCase):
    def setUp(self):
        self.index_url = reverse('index')

    def test_index_page(self):
        resp = self.client.get(self.index_url)
        self.assertEqual(resp.status_code, 200)

    def test_empty_form_submition(self):
        resp = self.client.post(self.index_url, data={})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.count(b'class="errorlist'), 4)
        self.assertIn(b'This field is required.', resp.content)

    def test_text_field_form_submition(self):
        data = {
            "name": "Vardenis",
            "surname": "Pavardenis",
            "birth_date": "2020-01-01",
        }

        resp = self.client.post(self.index_url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.count(b'class="errorlist'), 1)
        self.assertIn(b'This field is required.', resp.content)

    @mock.patch('requests.post')
    def test_form_submition_with_data_missmatching_document_data(self, post_mock):
        post_mock.return_value = ResponseMock(
            status_code=200,
            content=open('identity/fixtures/vigilija_realid_validation_content.json').read(),
        )

        data = {
            "name": "Vardenis",
            "surname": "Pavardenis",
            "birth_date": "2020-01-01",
            "document_picture": io.BytesIO(b'test_file_content'),
        }

        resp = self.client.post(self.index_url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist', resp.content)
        self.assertIn(b'Entered name missmatches name on the document.', resp.content)

    @mock.patch('requests.post')
    def test_successful_form_submition_with_vigilija_data(self, post_mock):
        post_mock.return_value = ResponseMock(
            status_code=200,
            content=open('identity/fixtures/vigilija_realid_validation_content.json').read(),
        )

        data = {
            "name": "Vigilija",
            "surname": "Bružaitė",
            "birth_date": "1978-03-11",
            "document_picture": io.BytesIO(b'Vigilija_passport_image_content'),
        }

        resp = self.client.post(self.index_url, data=data)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'You have entered correct information!', resp.content)
        self.assertNotIn(b'class="errorlist"', resp.content)
        self.assertNotIn(b'This field is required.', resp.content)
