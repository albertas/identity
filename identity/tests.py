from django.test import TestCase
from django.urls import reverse


class IdentityFormTestCase(TestCase):
    def test_index_page(self):
        index_url = reverse('index')
        resp = self.client.get(index_url)
        self.assertEqual(resp.status_code, 200)
