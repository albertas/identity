import base64
import hashlib

import requests

from django import forms
from django.conf import settings


class IdentityForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255)
    surname = forms.CharField(label='Surname', max_length=255)
    birth_date = forms.DateField()
    document_picture = forms.FileField()

    def encode_base64_and_sha1(self, content):
        # import ipdb; ipdb.set_trace()
        content_base64 = str(base64.b64encode(content), "utf-8")

        m = hashlib.sha1()
        m.update(content)
        content_sha1 = m.hexdigest()  # m.digest()
        return content_base64, content_sha1

    def clean_document_picture(self):
        document_picture = self.cleaned_data['document_picture']
        content = document_picture.read()
        document_picture.seek(0)

        content_base64, content_sha1 = self.encode_base64_and_sha1(content)

        validation_url = 'https://api.identiway.com/docs/validate'

        headers = {
            "Content-type": "application/json",
            "x-api-key": settings.REALID_API_KEY,
        }

        data = {
            "document": content_base64,
            "digest": content_sha1,
            "type": "lt_pass_rev",
        }

        resp = requests.post(url=validation_url, headers=headers, json=data)

        ocr_texts = resp.json().get('ocr_texts')
        if not ocr_texts:
            raise forms.ValidationError('Could not validate document image')

        return document_picture
