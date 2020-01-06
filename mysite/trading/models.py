from datetime import datetime
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
    earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    @receiver(post_save, sender=User)
    def update_user_profile(sender, instance, created, **kwargs):
        if created:
            Account.objects.create(user=instance)
        instance.account.save()


class Instrument(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'instrument'


class Country(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'country'


class Currency(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50, unique=True)
    rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal(0.00))
    country = models.ManyToManyField(Country, related_name='country_currency')
    base = models.BooleanField(default=False)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'currency'


class Exchange(models.Model):
    code = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=250, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'exchange'


class Stock(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, default=1)
    ticker = models.CharField(max_length=10)
    name = models.CharField(max_length=255, blank=True, null=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, default=1)
    favourite = models.ManyToManyField(User, related_name='favourite', blank=True)

    def __str__(self):
        return self.ticker

    def is_favourite(self, user):
        if self.favourite.filter(id=user.id).exists():
            return True

        return False

    def current_price(self):

        intraday = IntradayData.objects.filter(instrument=self).order_by('-timestamp')[:1]
        day = StockData.objects.filter(instrument=self).order_by('-timestamp')[:1]

        if intraday.exists() and day.exists():
            intraday = intraday.first()
            day = day.first()

            if intraday.timestamp > day.timestamp:
                return intraday
            else:
                return day

        elif intraday.exists():
            intraday = intraday.first()
            return intraday

        elif day.exists():
            day = day.first()
            return day

    class Meta:
        db_table = 'stock'
        constraints = [
            models.UniqueConstraint(fields=['ticker', 'name', 'exchange_id'], name='Company Stock')
        ]


class StockData(models.Model):
    timestamp = models.DateTimeField()
    instrument = models.ForeignKey(Stock, on_delete=models.CASCADE)

    high = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    low = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    open = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)
    adj_close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    dividend = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    split_coefficient = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(1.0))

    def __str__(self):
        string = self.instrument.ticker + ' ' + self.timestamp.strftime('%Y-%m-%d')
        return string

    class Meta:
        db_table = 'stock_data'
        unique_together = (('timestamp', 'instrument'),)


class IntradayData(models.Model):
    timestamp = models.DateTimeField()
    instrument = models.ForeignKey(Stock, on_delete=models.CASCADE)
    high = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    low = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    open = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)

    def __str__(self):
        string = self.instrument.ticker + ' ' + self.timestamp
        return string

    class Meta:
        db_table = 'intraday_data'
        unique_together = (('timestamp', 'instrument'),)


class Position(models.Model):
    DIRECTION_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    instrument = models.ForeignKey(Stock, on_delete=models.CASCADE)
    open_date = models.DateTimeField(default=datetime.now)
    close_date = models.DateTimeField(default=None, blank=True, null=True)

    quantity = models.IntegerField(default=1)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    result = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    open = models.BooleanField(default=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'positions'
