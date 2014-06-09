test:
	django-admin.py test --settings=secureauth.test_settings secureauth
coverage:
	export DJANGO_SETTINGS_MODULE=secureauth.test_settings && \
	coverage run --branch --source=secureauth `which django-admin.py` test secureauth && \
	coverage report --omit="secureauth/test*,secureauth/migrations/*,secureauth/management/*"
sphinx:
	cd docs && sphinx-build -b html -d .build/doctrees . .build/html
pep8:
	flake8 --exclude=migrations secureauth
open_docs:
	open docs/.build/html/index.html
run_server:
	cd demo && HTTPS=on python manage.py runsslserver --traceback 1> /dev/null
run_celery:
	cd demo && python manage.py celeryd --loglevel=info >& /tmp/celery.log &
run_shell:
	cd demo && python manage.py shell_plus --print-sql
run_redis:
	redis-server >& /dev/null &
makemessages:
	cd demo && python manage.py makemessages --all --no-location --symlinks
compilemessages:
	cd demo && python manage.py compilemessages
