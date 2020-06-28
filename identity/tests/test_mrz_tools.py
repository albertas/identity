import json

from parameterized import parameterized

from django.test import TestCase

from identity.mrz_tools import get_mrz, extract_mrz_data_from_mrz


class MRZToolsTestCase(TestCase):
    @parameterized.expand([
        (
            ["2016", "PECIMEN\nP<LTUBASANAVICIENE<<BIRUTE<<<<<<<<<<<<<<<<<<\n00000000<OLTU5911239F160828545911231023<<<10\n"],
            "P<LTUBASANAVICIENE<<BIRUTE<<<<<<<<<<<<<<<<<<00000000<0LTU5911239F160828545911231023<<<10",
        ),
        (
            ["PECIMEN\nP\n<\nLTUBASANAVICIENE\n<<\nBIRUTE\n<<<<<<<<<<<<<<<<<<\n00000000\n<\nOLTU5911239F160828545911231023\n<<<\n10\nLETAVAS\n"],
            None,
        ),
        (
            ["Brunaite\n*\nP<LTUBRUZAITE<<VIGILIJA<<<<\n\u304f\u304f\u304f\u304f\u304f\u304f\u304f\u304f\u304f\u304f\u3001\n00000000<OLTU7803118 F210127747803111025<<<64\nLIETUVOS\n"],
            "P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64",
        ),
        (
            ["Bouzoute\nEL\nP<LTUBRUZAITE<<VIGILIJA<<<<\n<<<<<\n00000000<OLTU7803118 F210127747803111025<<<64\n"],
            "P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64",
        ),
        (
            json.load(open('identity/fixtures/birute_realid_validation_content.json'))['ocr_texts'],
            "P<LTUBASANAVICIENE<<BIRUTE<<<<<<<<<<<<<<<<<<00000000<0LTU5911239F160828545911231023<<<10",
        ),
        (
            json.load(open('identity/fixtures/vigilija_realid_validation_content.json'))['ocr_texts'],
            "P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64",
        ),
    ])
    def test_mrz_detection(self, ocr_texts, mrz):
        self.assertEqual(get_mrz(ocr_texts), mrz)


    @parameterized.expand([
        (
            "P<LTUBASANAVICIENE<<BIRUTE<<<<<<<<<<<<<<<<<<00000000<0LTU5911239F160828545911231023<<<10",
            {
                'birth_check_digit': '9',
                'check_digit': '0',
                'date_of_birth': '591123',
                'expiration_date': '160828',
                'expiration_date_check_digit': '5',
                'issuing_country': 'LTU',
                'names': 'BIRUTE',
                'nationality': 'LTU',
                'passport_indicator': 'P',
                'passport_number': '00000000',
                'passport_number_check_digit': '0',
                'passport_type': '',
                'personal_number': '45911231023',
                'personal_number_check_digit': '1',
                'sex': 'F',
                'surname': 'BASANAVICIENE',
                'td3': 'P<LTUBASANAVICIENE<<BIRUTE<<<<<<<<<<<<<<<<<<00000000<0LTU5911239F160828545911231023<<<10'
            }
        ),
        (
            "P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64",
            {
                'birth_check_digit': '8',
                'check_digit': '4',
                'date_of_birth': '780311',
                'expiration_date': '210127',
                'expiration_date_check_digit': '7',
                'issuing_country': 'LTU',
                'names': 'VIGILIJA',
                'nationality': 'LTU',
                'passport_indicator': 'P',
                'passport_number': '00000000',
                'passport_number_check_digit': '0',
                'passport_type': '',
                'personal_number': '47803111025',
                'personal_number_check_digit': '6',
                'sex': 'F',
                'surname': 'BRUZAITE',
                'td3': 'P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64'
            }
        ),
        (
            "P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64",
            {
                'birth_check_digit': '8',
                'check_digit': '4',
                'date_of_birth': '780311',
                'expiration_date': '210127',
                'expiration_date_check_digit': '7',
                'issuing_country': 'LTU',
                'names': 'VIGILIJA',
                'nationality': 'LTU',
                'passport_indicator': 'P',
                'passport_number': '00000000',
                'passport_number_check_digit': '0',
                'passport_type': '',
                'personal_number': '47803111025',
                'personal_number_check_digit': '6',
                'sex': 'F',
                'surname': 'BRUZAITE',
                'td3': 'P<LTUBRUZAITE<<VIGILIJA<<<<<<<<<00000000<0LTU7803118F210127747803111025<<<64'
             }
        ),
    ])
    def test_mrz_data_extraction(self, mrz_str, mrz_data):
        self.assertEqual(extract_mrz_data_from_mrz(mrz_str), mrz_data)
