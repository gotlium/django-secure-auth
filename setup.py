# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from secureauth import get_version


setup(
    name='django-secure-auth',
    version=get_version(),
    description='Secure authentication by TOTP, SMS, Codes & Question',
    keywords='django secure auth protection totp sms codes question',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    author="GoTLiuM InSPiRiT",
    author_email='gotlium@gmail.com',
    url='https://github.com/gotlium/django-secure-auth',
    license='GPL v3',
    packages=find_packages(exclude=['demo']),
    include_package_data=True,
    package_data={'secureauth': [
        'templates/secureauth/*.html',
        'templates/secureauth/codes_settings/*.html',
        'templates/secureauth/phone_settings/*.html',
        'templates/secureauth/question_settings/*.html',
        'templates/secureauth/totp_settings/*.html',
        'locale/*/LC_MESSAGES/*.po'
        'static/secureauth/js/*.js'
    ]},
    zip_safe=False,
    install_requires=[
        'pyotp>=1.3.1',
        'httpagentparser>=1.5.0',
        'django-tables2>=0.14.0',
        'django-filter>=0.7',
        'phonenumbers>=6.1.0',
        'django-simple-captcha>=0.4.2',
        'django-ipware>=0.0.8',
        'slowaes==0.1a1',
        'ipaddress>=1.0.6',
        'django-phonenumber-field>=0.5',
    ]
)
