# Generated by Django 2.2.7 on 2019-12-11 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0005_delete_marketdata'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('high', models.FloatField(blank=True, null=True)),
                ('low', models.FloatField(blank=True, null=True)),
                ('open', models.FloatField(blank=True, null=True)),
                ('close', models.FloatField(blank=True, null=True)),
                ('volume', models.IntegerField(blank=True, null=True)),
                ('adj_close', models.FloatField(blank=True, null=True)),
                ('ticker', models.ForeignKey(db_column='ticker', on_delete=django.db.models.deletion.CASCADE, to='trading.Stock')),
            ],
            options={
                'db_table': 'market_data',
                'unique_together': {('date', 'ticker')},
            },
        ),
    ]
