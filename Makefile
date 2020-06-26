prepare_environment: venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip check

venv:
	python3 -m venv venv

run: 
	venv/bin/python manage.py runserver --settings identity.settings

test:
	venv/bin/python manage.py test --settings identity.settings
