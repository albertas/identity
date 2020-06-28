from datetime import datetime

from django import forms

from identity.mrz_tools import (
    get_ocr_text,
    extract_mrz_data,
    to_upper_ascii,
)


class IdentityForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255)
    surname = forms.CharField(label='Surname', max_length=255)
    birth_date = forms.DateField()
    document_picture = forms.FileField()

    def clean(self):
        cleaned_data = super().clean()

        if 'document_picture' not in cleaned_data:
            return

        document_picture = cleaned_data['document_picture']
        content = document_picture.read()
        document_picture.seek(0)

        ocr_text = get_ocr_text(content)
        if not ocr_text:
            msg = 'Could not validate data, because failed to call RealID API.'
            raise forms.ValidationError(msg)

        mrz_data = extract_mrz_data(ocr_text)

        if not mrz_data:
            msg = 'Could not validate data, because failed to parse info from image.'
            raise forms.ValidationError(msg)

        # Extracted data
        mr_name = mrz_data['names']
        mr_surname = mrz_data['surname']
        mr_country = mrz_data['issuing_country']
        mr_birth_date = mrz_data['date_of_birth']
        mr_personal_code = mrz_data['personal_number']

        # Entered data
        entered_name = cleaned_data['name']
        entered_surname = cleaned_data['surname']
        entered_birth_date = cleaned_data['birth_date']

        # Unified format enetered data
        entered_name_upper_ascii = to_upper_ascii(entered_name)
        entered_surname_upper_ascii = to_upper_ascii(entered_surname)
        entered_birth_date_YYMMDD = datetime.strftime(entered_birth_date, '%y%m%d')

        if entered_name_upper_ascii != mr_name:
            raise forms.ValidationError('Entered name missmatches name on the document.')

        if entered_surname_upper_ascii!= mr_surname:
            raise forms.ValidationError('Entered surname missmatches surname on the document.')

        if entered_birth_date_YYMMDD != mr_birth_date:
            raise forms.ValidationError('Entered birth date missmatches birth date on the document.')
