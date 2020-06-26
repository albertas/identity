from django import forms


class IdentityForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255)
    surname = forms.CharField(label='Surname', max_length=255)
    birth_date = forms.DateField()
    document_picture = forms.FileField()
