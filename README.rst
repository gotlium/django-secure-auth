Django-Secure-Auth
==================

Demo installation:
------------------

.. code-block:: bash

    $ sudo apt-get install geoip-database-contrib redis-server
    $ mkvirtualenv django-secure-auth
    $ git clone https://github.com/gotlium/django-secure-auth.git
    $ cd django-secure-auth
    $ pip install -r requirements.txt
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py syncdb --noinput
    $ python manage.py migrate


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


Now you can open http://127.0.0.1:8000/accounts/register/ and register
new account and setup all available authentication methods.

*Note: activation link will be output to console.*


Screenshots
-----------
.. image:: /screenshots/login-confirmation.jpg
.. image:: /screenshots/settings.jpg
.. image:: /screenshots/two-factor-configuration.jpg
.. image:: /screenshots/sms-settings.jpg


.. image:: https://d2weczhvl823v0.cloudfront.net/gotlium/django-secure-auth/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
