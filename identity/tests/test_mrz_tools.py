from parameterized import parameterized

from django.test import TestCase

from identity.mrz_tools import get_mrz


class MRZDetectionTestCase(TestCase):
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
    ])
    def test_mrz_detection(self, ocr_str, mrz):
        self.assertEqual(get_mrz(ocr_str), mrz)
