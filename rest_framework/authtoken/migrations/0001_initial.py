# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(verbose_name='Key',primary_key=True, serialize=False, max_length=40)),
                ('created', models.DateTimeField(verbose_name='Created',auto_now_add=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, verbose_name='User', related_name='auth_token')),
            ],
            options={
		'verbose_name_plural': 'Tokens',
		'verbose_name': 'Token'
            },
            bases=(models.Model,),
        ),
    ]
