# Generated by Django 2.1 on 2019-09-13 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('minefield', '0002_auto_20190907_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='password',
            field=models.CharField(default='', max_length=32),
        ),
        migrations.AddField(
            model_name='person',
            name='type',
            field=models.CharField(default='student', max_length=16, unique=True),
        ),
    ]
