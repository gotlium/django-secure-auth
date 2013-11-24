# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from secureauth import get_version


setup(
    name='django-secure-auth',
    version=get_version('b1'),
    description='Django Secure auth by TOTP, SMS, Codes & Question',
    keywords='django secure auth totp sms codes question',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
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
    ]},
    zip_safe=False,
    install_requires=[
        'pyotp>=1.3.1',
        'twilio>=3.6.4',
        'httpagentparser>=1.5.0',
        'django-tables2>=0.14.0',
        'django-filter>=0.7',
    ]
)
