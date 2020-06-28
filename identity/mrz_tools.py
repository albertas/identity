import base64
import hashlib
import re
import unicodedata

import requests

from django.conf import settings


alpha = '[^\W1-9_]'
alpha_lt = f'({alpha}|<)'
num = '\d'
num_lt = f'({num}|<)'
alpha_num_lt = f'([^\W_]|<)'

td3_parts = {
    'passport_indicator': f'{alpha_lt}{{1}}',
    'passport_type': f'{alpha_lt}{{1}}',
    'issuing_country': f'{alpha_lt}{{3}}',
    'surname': f'{alpha}{{0,37}}',  # OCR skips some < signs so allow less chars
    'suname_name_separator': f'<<',
    'names': f'{alpha_lt}{{0,37}}',  # OCR skips some < signs so allow less chars
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

td3_parts_pattern = ''.join([f'(?P<{name}>{pattern})' for name, pattern in td3_parts.items()])
td3_pattern = f'^(?P<td3>{td3_parts_pattern})'


def encode_base64_and_sha1(content):
    content_base64 = str(base64.b64encode(content), "utf-8")
    m = hashlib.sha1()
    m.update(content)
    content_sha1 = m.hexdigest()
    return content_base64, content_sha1


def get_ocr_texts(content):
    '''Encodes and posts file content to RealID API in order to retrieve OCR texts'''
    content_base64, content_sha1 = encode_base64_and_sha1(content)

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

    if resp.ok:
        return resp.json().get('ocr_texts')


def remove_noise_from_ocr_string(ocr_str):
    '''Fixes incorrectly recognized characters'''
    char_fixes = {
        '\u3001': '',
        ' ': '',
        '\u304f': '<',
        'O': '0',  # OCR sometimes missmatches 0 with O and visa versa
                   # So we replace O with 0s to avoid problems with numbers
                   # When text is expected 0s will be replaced to Os
    }

    for chr_from, chr_to in char_fixes.items():
        ocr_str = ocr_str.replace(chr_from, chr_to)
    return ocr_str


def extract_mrz(ocr_texts):
    # Surname and name has to be strictly separated by <<
    # So find << and search for first \n to the right before checking td3 pattern
    surname_name_sep_pattern = f'{alpha}{{1}}\s*<\s*<\s*{alpha}{{1}}'

    ocr_texts_str = '\n'.join(ocr_texts)
    ocr_str = remove_noise_from_ocr_string(ocr_texts_str)

    mrz_matches = []
    for sep_match in re.finditer(surname_name_sep_pattern, ocr_str):
        mrz_start_index = ocr_str[:sep_match.start()].rfind('\n')

        ocr_str_without_newlines = ocr_str[mrz_start_index:].replace('\n', '')

        match = re.search(td3_pattern, ocr_str_without_newlines)
        if match:
            mrz_matches.append(match.groupdict()['td3'])

    if mrz_matches:
        return sorted(mrz_matches, key=lambda x: len(x))[-1]


def extract_mrz_data_from_mrz(mrz):
    '''Returns dictionary with MRZ data extracted from MRZ'''
    match = re.search(td3_pattern, mrz)
    if match:
        mrz_data = match.groupdict()
        mrz_data.pop('suname_name_separator')
        mrz_data.pop('td3')

        not_num_keys = [
            'passport_indicator',
            'passport_type',
            'issuing_country',
            'surname',
            'names',
            'nationality',
            'sex',
        ]

        for key in mrz_data:
            mrz_data[key] = mrz_data[key].strip('<')
            if key in not_num_keys:
                mrz_data[key] = mrz_data[key].replace('0', 'O')

        return mrz_data


def extract_mrz_data(ocr_texts):
    '''Returns dictionary with MRZ data extracted from OCR texts'''
    mrz = extract_mrz(ocr_texts)
    mrz_data = extract_mrz_data_from_mrz(mrz)
    return mrz_data


def to_upper_ascii(value):
    '''Converts UTF-8 string into upper-cased ASCII string'''
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    return value.decode().upper()
