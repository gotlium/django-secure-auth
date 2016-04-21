# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAuthActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.CharField(max_length=40, db_index=True)),
                ('geo', models.CharField(max_length=255, null=True, verbose_name='GEO', blank=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('agent', models.CharField(max_length=255, null=True, verbose_name='Browser', blank=True)),
                ('confirm_method', models.CharField(blank=True, max_length=10, null=True, verbose_name='Confirm Method', choices=[(b'', b'---'), (b'code', 'by code'), (b'token', 'by token'), (b'phone', 'by sms'), (b'question', 'by question')])),
                ('notified', models.BooleanField(default=False, editable=False)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='UserAuthAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.BigIntegerField(unique=True)),
                ('attempt', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.TextField()),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('last_verified', models.DateTimeField(verbose_name='Last verified', null=True, editable=False, blank=True)),
                ('number', models.TextField(null=True, verbose_name='Number', blank=True)),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserAuthIP',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthIPRange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_data', models.CharField(help_text=b'xxx.xxx.xxx.xxx or xxx.xxx.xxx.xxx/24', max_length=18, verbose_name='IP/IP range')),
                ('is_ip', models.BooleanField(default=False, verbose_name='Is IP')),
                ('ip', models.ForeignKey(editable=False, to='secureauth.UserAuthIP')),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthLogging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserAuthPhone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.TextField()),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('last_verified', models.DateTimeField(verbose_name='Last verified', null=True, editable=False, blank=True)),
                ('phone', models.CharField(unique=True, max_length=255, verbose_name='Phone')),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserAuthQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.TextField()),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('last_verified', models.DateTimeField(verbose_name='Last verified', null=True, editable=False, blank=True)),
                ('question', models.TextField(verbose_name='Question')),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserAuthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.TextField()),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('last_verified', models.DateTimeField(verbose_name='Last verified', null=True, editable=False, blank=True)),
                ('user', models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='userauthiprange',
            unique_together=set([('ip', 'ip_data', 'is_ip')]),
        ),
    ]
