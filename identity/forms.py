import base64
import hashlib
import re

import requests

from django import forms
from django.conf import settings


class IdentityForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255)
    surname = forms.CharField(label='Surname', max_length=255)
    birth_date = forms.DateField()
    document_picture = forms.FileField()

    def encode_base64_and_sha1(self, content):
        content_base64 = str(base64.b64encode(content), "utf-8")
        m = hashlib.sha1()
        m.update(content)
        content_sha1 = m.hexdigest()
        return content_base64, content_sha1

    def clean_noise(self, ocr_str):
        char_fixes = {
            "\u3001": "",
            " ": "",
            "\n": "",
            "\u304f": ">",
            "O": "0",  # OCR sometimes missrecognizes
                       # Should add this digit to alpha definition
        }

        for chr_from, chr_to in char_fixes.items():
            ocr_str = ocr_str.replace(chr_from, chr_to)
        return ocr_str

    def extract_mrz_data(self, ocr_texts):
        ocr_str = ''.join(ocr_texts)
        ocr_str = self.clean_noise(ocr_str)

        alpha = '[^\W1-9_]'
        alpha_lt = f'({alpha}|<)'
        num = '\d'
        num_lt = f'({num}|<)'
        alpha_num_lt = f'([^\W_]|<)'

        td3_parts = {
            'passport_indicator': f'P{{1}}',  # TODO: Add support for not passport documents
            'passport_type': f'{alpha_lt}{{1}}',
            'issuing_country': f'{alpha_lt}{{3}}',
            'surname': f'{alpha}{{0,37}}',
            'suname_name_separator': f'<<',
            'names': f'{alpha_lt}{{0,37}}',
            'passport_number': f'{alpha_num_lt}{{9}}',
            'passport_number_check_digit': f'{num}{{1}}',
            'nationality': f'{alpha_lt}{{3}}',
            'date_of_birth': f'{num}{{1,6}}',
            'birth_check_digit': f'{num}{{1}}',
            'sex': f'{alpha_lt}{{1}}',
            'expiration_date': f'{num}{{6}}',
            'expiration_date_check_digit': f'{num}{{1}}',
            'personal_number': f'{alpha_num_lt}{{14}}',
            'personal_number_check_digit': f'{num}{{1}}',
            'check_digit': f'{num}{{1}}',
        }
        td3_pattern = ''.join([f'(?P<{name}>{pattern})' for name, pattern in td3_parts.items()])

        match = re.search(f'(?P<td3>{td3_pattern})', ocr_str)
        if not match:
            return None
        return match.groupdict()

    def clean(self):
        cleaned_data = super().clean()

        if 'document_picture' not in cleaned_data:
            return

        document_picture = cleaned_data['document_picture']
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
            msg = 'Could not validate data, because failed to call RealID API.'
            raise forms.ValidationError(msg)

        mrz_data = self.extract_mrz_data(ocr_texts)
        if not mrz_data:
            msg = 'Could not validate data, because failed to parse info from image.'
            raise forms.ValidationError(msg)

        # Extracted data
        name = mrz_data['names'].strip('<')
        surname = mrz_data['surname'].strip('<')
        country = mrz_data['issuing_country']
        birth_date = mrz_data['date_of_birth']
        personal_code = mrz_data['personal_number']

        # TODO: Compare the extracted data with user enetered data

