from django.shortcuts import render

from identity.forms import IdentityForm


def index(request):
    if request.method == 'POST':
        form = IdentityForm(request.POST, request.FILES)
        if form.is_valid():
            return render(request, 'identity/identity_form.html', {
                'form': IdentityForm(),
                'message': 'You have entered correct information!',
                'mrz_data': form.mrz_data,
            })
    else:
        form = IdentityForm()
    return render(request, 'identity/identity_form.html', {
        'form': form,
        'mrz_data': form.mrz_data,
    })
