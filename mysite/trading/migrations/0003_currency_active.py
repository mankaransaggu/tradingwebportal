# Generated by Django 3.0.2 on 2020-01-27 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0002_auto_20200127_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
