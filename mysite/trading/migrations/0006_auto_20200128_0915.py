# Generated by Django 3.0.2 on 2020-01-28 09:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0005_auto_20200127_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockpricedata',
            name='data_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trading.DataType'),
        ),
    ]
