from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    @receiver(post_save, sender=User)
    def update_user_profile(sender, instance, created, **kwargs):
        if created:
            Account.objects.create(user=instance)
        instance.account.save()


class Country (models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'country'


class Exchange(models.Model):
    code = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=250, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'exchange'


class Stock(models.Model):
    ticker = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=255, blank=True, null=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, default=1)
    favourite = models.ManyToManyField(User, related_name='favourite', blank=True)

    def __str__(self):
        return self.ticker

    class Meta:
        db_table = 'stock'


class MarketData(models.Model):
    date = models.DateField()
    instrument = models.ForeignKey(Stock, on_delete=models.CASCADE, db_column='ticker')

    high_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    low_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    open_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)
    adj_close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    def __str__(self):
        string = self.instrument.ticker + ' ' + self.date.strftime('%Y-%m-%d')
        return string

    class Meta:
        db_table = 'market_data'
        unique_together = (('date', 'instrument'),)


class Position(models.Model):

    DIRECTION_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    instrument = models.ForeignKey(Stock, on_delete=models.CASCADE)
    open_date = models.DateField(default=None, blank=True, null=True)
    close_date = models.DateField(default=None, blank=True, null=True)

    quantity = models.IntegerField(default=1)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    result = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    open = models.BooleanField(default=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'positions'
