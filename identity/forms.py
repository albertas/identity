import base64
import hashlib
import re
import unicodedata
from datetime import datetime

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

    def remove_noise_from_ocr_string(self, ocr_str):
        '''Fixes incorrectly recognized characters'''
        char_fixes = {
            '\u3001': '',
            ' ': '',
            '\n': '',
            '\u304f': '>',
            'O': '0',  # OCR sometimes missmatches 0 with O and visa versa
                       # So we replace O with 0s to avoid problems with numbers
                       # When text is expected 0s will be replaced to Os
        }

        for chr_from, chr_to in char_fixes.items():
            ocr_str = ocr_str.replace(chr_from, chr_to)
        return ocr_str

    def extract_mrz_data(self, ocr_texts):
        '''Finds and extracts machine readable data in TD3 format from OCR texts'''
        ocr_str = ''.join(ocr_texts)
        ocr_str = self.remove_noise_from_ocr_string(ocr_str)

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

    def get_ocr_texts(self, content):
        '''Encodes and posts file content to RealID API in order to retrieve OCR texts'''
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
        return ocr_texts

    def to_upper_ascii(self, value):
        '''Converts UTF-8 string into upper-cased ASCII string'''
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        return value.decode().upper()

    def clean(self):
        cleaned_data = super().clean()

        if 'document_picture' not in cleaned_data:
            return

        document_picture = cleaned_data['document_picture']
        content = document_picture.read()
        document_picture.seek(0)

        ocr_texts = self.get_ocr_texts(content)
        if not ocr_texts:
            msg = 'Could not validate data, because failed to call RealID API.'
            raise forms.ValidationError(msg)

        mrz_data = self.extract_mrz_data(ocr_texts)
        if not mrz_data:
            msg = 'Could not validate data, because failed to parse info from image.'
            raise forms.ValidationError(msg)

        # Extracted data
        mr_name = mrz_data['names'].strip('<').replace('0', 'O')
        mr_surname = mrz_data['surname'].strip('<').replace('0', 'O')
        mr_country = mrz_data['issuing_country'].strip('<')
        mr_birth_date = mrz_data['date_of_birth']
        mr_personal_code = mrz_data['personal_number'].strip('<')

        # Entered data
        entered_name = cleaned_data['name']
        entered_surname = cleaned_data['surname']
        entered_birth_date = cleaned_data['birth_date']

        # Unified format enetered data
        entered_name_upper_ascii = self.to_upper_ascii(entered_name)
        entered_surname_upper_ascii = self.to_upper_ascii(entered_surname)
        entered_birth_date_YYMMDD = datetime.strftime(entered_birth_date, '%y%m%d')

        if entered_name_upper_ascii != mr_name:
            raise forms.ValidationError('Entered name missmatches name on the document.')

        if entered_surname_upper_ascii!= mr_surname:
            raise forms.ValidationError('Entered surname missmatches surname on the document.')

        if entered_birth_date_YYMMDD != mr_birth_date:
            raise forms.ValidationError('Entered birth date missmatches birth date on the document.')
