from datetime import datetime
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class Currency(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'currency'


class Country(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)
    currency = models.ForeignKey(Currency, related_name='country_base', on_delete=models.CASCADE)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'country'


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    country = models.ForeignKey(Country, related_name='user_country', on_delete=models.CASCADE, default=1)
    base_currency = models.ForeignKey(Currency, related_name='user_currency', on_delete=models.CASCADE, default=1)

    value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    result = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    @receiver(post_save, sender=User)
    def update_user_profile(sender, instance, created, **kwargs):
        if created:
            Account.objects.create(user=instance)
        instance.account.save()


class Exchange(models.Model):
    code = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=250, unique=True)
    country = models.ForeignKey(Country, related_name='exchange_country', on_delete=models.CASCADE)

    def __str__(self):
        return self.code

    def get_currency(self):
        country = Country.objects.get(id=self.country)
        currency = Currency.objects.get(id=country.currency)
        return currency

    class Meta:
        db_table = 'exchange'


class Instrument(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'instrument'


class Stock(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='stock_instrument', on_delete=models.CASCADE, default=1)
    ticker = models.CharField(max_length=10)
    name = models.CharField(max_length=255, blank=True, null=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, default=1)
    favourite = models.ManyToManyField(User, related_name='favourite_stock', blank=True)

    def __str__(self):
        return self.ticker

    def is_favourite(self, user):
        if self.favourite.filter(id=user.id).exists():
            return True

        return False

    def current_data(self):
        data = StockPriceData.objects.filter(stock=self).first()
        return data

    def get_currency(self):
        exchange = Exchange.objects.filter(id=self.exchange)
        country = Country.objects.filter(id=exchange.country)
        currency = Currency.objects.filter(id=country.currency)

        return currency

    class Meta:
        db_table = 'stock'
        constraints = [
            models.UniqueConstraint(fields=['ticker', 'name', 'exchange_id'], name='Company Stock')
        ]


class StockPriceData(models.Model):
    timestamp = models.DateTimeField()
    stock = models.ForeignKey(Stock, related_name='stock_data', on_delete=models.CASCADE)
    high = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    low = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    open = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)
    adj_close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    dividend = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    split_coefficient = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(1.0))

    def __str__(self):
        string = self.instrument.ticker + ' ' + self.timestamp
        return string

    class Meta:
        db_table = 'stock_price_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'stock']),
        ]


class FX(models.Model):
    code = models.CharField(max_length=10, unique=True)
    from_currency = models.ForeignKey(Currency, related_name='from_currency', on_delete=models.CASCADE, default=1)
    to_currency = models.ForeignKey(Currency, related_name='to_currency', on_delete=models.CASCADE, default='2')
    instrument = models.ForeignKey(Instrument, related_name='fx_instrument', default=1, on_delete=models.CASCADE)
    favourite = models.ManyToManyField(User, related_name='favourite_fx', blank=True)

    def __str__(self):
        return self.code

    # def save(self, *args, **kwargs):
    #     if not self.code:
    #         self.code = self.base_currency + '/' + self.exchange_currency
    #     super.save(*args, **kwargs)

    def is_favourite(self, user):
        if self.favourite.filter(id=user.id).exists():
            return True

        return False

    def current_data(self):
        data = FXPriceData.objects.filter(stock=self).first()
        return data

    class Meta:
        db_table = 'fx_pair'
        indexes = [
            models.Index(fields=['from_currency', 'to_currency']),
        ]


class FXPriceData(models.Model):
    timestamp = models.DateTimeField()
    currency_pair = models.ForeignKey(FX, related_name='currency_pair', on_delete=models.CASCADE)
    high = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    low = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    open = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)

    def __str__(self):
        string = self.currency_pair.code + ' ' + self.timestamp
        return string

    class Meta:
        db_table = 'fx_price_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'currency_pair']),
        ]


class Position(models.Model):
    DIRECTION_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    open_date = models.DateTimeField(default=datetime.now)
    close_date = models.DateTimeField(default=None, blank=True, null=True)

    quantity = models.IntegerField(default=1)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    result = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    open = models.BooleanField(default=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    stock = models.ForeignKey(Stock, null=True, blank=True, on_delete=models.CASCADE)
    fx = models.ForeignKey(FX, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def instrument(self):
        return self.stock or self.fx

    @instrument.setter
    def instrument(self, obj):
        if type(obj) == Stock:
            self.stock = obj
            self.fx = None
        elif type(obj) == FX:
            self.stock = None
            self.fx = obj
        else:
            raise ValueError('obj parameter must be a Stock, FX, Bond, Indicie class')

    def current_result(self):
        if self.stock is None:
            fx = FX.objects.filter.get(id=self.fx.id)
            current_data = fx.current_data()
            result = current_data.close - self.open_price

        elif self.fx is None:
            stock = Stock.objects.get(id=self.stock.id)
            current_data = stock.current_data()
            result = current_data.close - self.open_price

        return result

    class Meta:
        db_table = 'positions'

