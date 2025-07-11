from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupObjectPermission',
            fields=[
                ('id', models.AutoField(primary_key=True,
                                        serialize=False, auto_created=True, verbose_name='ID')),
                ('object_pk', models.CharField(
                    max_length=255, verbose_name='object ID')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('group', models.ForeignKey(to='auth.Group', on_delete=models.CASCADE)),
                ('permission', models.ForeignKey(to='auth.Permission', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserObjectPermission',
            fields=[
                ('id', models.AutoField(primary_key=True,
                                        serialize=False, auto_created=True, verbose_name='ID')),
                ('object_pk', models.CharField(
                    max_length=255, verbose_name='object ID')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('permission', models.ForeignKey(to='auth.Permission', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userobjectpermission',
            unique_together={('user', 'permission', 'object_pk')},
        ),
        migrations.AlterUniqueTogether(
            name='groupobjectpermission',
            unique_together={('group', 'permission', 'object_pk')},
        ),
    ]
