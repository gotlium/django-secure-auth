clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

pep8:
	flake8 --exclude=migrations secureauth

run:
	cd demo && python manage.py runserver_plus --print-sql

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

release: clean
	python setup.py register sdist upload --sign
	python setup.py bdist_wheel upload --sign
