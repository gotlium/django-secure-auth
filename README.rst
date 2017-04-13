Django-Secure-Auth
==================

.. image:: https://landscape.io/github/gotlium/django-secure-auth/master/landscape.svg
   :target: https://landscape.io/github/gotlium/django-secure-auth/master
   :alt: Code Health
.. image:: https://api.codacy.com/project/badge/grade/e1788d6ac7ca437aa6bbb3abfdf19dce
    :target: https://www.codacy.com/app/gotlium/django-secure-auth
    :alt: Codacy
.. image:: https://img.shields.io/badge/python-2.7-blue.svg
    :alt: Python 2.7, 3.4+
    :target: https://pypi.python.org/pypi/django-secure-auth/
.. image:: https://img.shields.io/pypi/v/django-secure-auth.svg
    :alt: Current version on PyPi
    :target: https://pypi.python.org/pypi/django-secure-auth/
.. image:: https://img.shields.io/pypi/dm/django-secure-auth.svg
    :alt: Downloads from PyPi
    :target: https://pypi.python.org/pypi/django-secure-auth/
.. image:: https://img.shields.io/badge/license-GPLv3-green.svg
    :target: https://pypi.python.org/pypi/django-secure-auth/
    :alt: License

Module which provide secure authentication by TOTP/SMS/Codes/Question.
Login protected by IP ranges and with captcha, when login attempt will fail.


Demo installation:
------------------

.. code-block:: bash

    $ sudo apt-get install -y virtualenvwrapper redis-server git python-dev || brew install pyenv-virtualenvwrapper redis git geoip
    $ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh || source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv django-secure-auth
    $ workon django-secure-auth
    $ git clone --depth 1 https://github.com/gotlium/django-secure-auth.git
    $ cd django-secure-auth
    $ pip install -r requirements.txt
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py syncdb --noinput
    $ python manage.py migrate --noinput
    $ python manage.py createsuperuser --username admin --email admin@local.host
    $ wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
    $ gunzip GeoLiteCity.dat.gz
    $ mkdir -p /usr/share/geoip/; mv GeoLiteCity.dat /usr/share/geoip/
    $ cd ../


Open settings:

.. code-block:: bash

    $ vim demo/settings.py


Replace Twilio credentials in ``AUTH_SMS_BACKEND_AUTH`` to your demo account settings or change SMS_FORCE to False.

Run Redis server and Celery daemon(or remove 'djcelery' from ``INSTALLED_APPS``):

.. code-block:: bash

    $ make run_redis
    $ make run_celery


Run test server:

.. code-block:: bash

    $ make run_server


Now you can open https://127.0.0.1:8000/accounts/register/ and register
new account and setup all available authentication methods.

*Note: activation link will be output to console.*


Crontab
-------

When you are using TOTP auth method, please update your server time.
If your server time is behind from real time, user cannot be authenticated by authenticator app.
You can run ntpd clients, or update time on server by cron job:

.. code-block:: bash

    SHELL=/bin/bash
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games
    MAILTO=root@localhost

    # Update time
    0 */6 * * * ntpdate ntp.ubuntu.com >& /dev/null


Screenshots
-----------
.. image:: /screenshots/login-confirmation.jpg
.. image:: /screenshots/settings.jpg
.. image:: /screenshots/two-factor-configuration.jpg
.. image:: /screenshots/sms-settings.jpg


Compatibility
-------------
* Python: 2.7
* Django: 1.4, 1.8
