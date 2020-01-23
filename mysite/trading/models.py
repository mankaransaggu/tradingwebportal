import uuid
from datetime import datetime
from decimal import Decimal

import django
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models import UniqueConstraint, signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


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


class UserAccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email address must be provided')

        if not password:
            raise ValueError('Password must be provided')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = UserAccountManager()

    email = models.EmailField('email', unique=True, blank=False, null=False)
    first_name = models.CharField('first_name', blank=False, null=False, max_length=100)
    last_name = models.CharField('first_name', blank=False, null=False, max_length=100)

    value = models.DecimalField('account_value', blank=False, null=False, decimal_places=2, max_digits=12, default=0)
    result = models.DecimalField('account_result', blank=True, null=False, decimal_places=2, max_digits=12, default=0)
    live_result = models.DecimalField('live_result', blank=False, null=False, decimal_places=2, max_digits=12, default=0)

    is_verified = models.BooleanField('verified', default=False)
    verification_uuid = models.UUIDField('Unique Verification UUID', default=uuid.uuid4)

    is_staff = models.BooleanField('staff_status', default=False)
    is_active = models.BooleanField('active', default=True)
    date_joined = models.DateTimeField('date_joined', default=django.utils.timezone.now)
    last_login = models.DateTimeField('last_login', default=django.utils.timezone.now)

    def __unicode__(self):
        return self.email

    def live_result(self):
        open_positions = Position.objects.filter(user=self, open=True)

        for pos in open_positions:

            self.live_result = self.live_result + pos.result
            print(self.live_result)
            self.save()


def account_post_save(sender, instance, signal, *arg, **kwargs):
    if not instance.is_verified:
        print(instance.email)
        send_mail(
            'Verify your trading account',
            'Click this link to verify: '
            'http://localhost:8000%s' % reverse('verify', kwargs={'uuid': str(instance.verification_uuid)}),
            'Baker Financial',
            [instance.email],
            fail_silently=False,
        )


signals.post_save.connect(account_post_save, sender=User)


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

    def get_stock_count(self):
        return self.listed_exchange.count()

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
    exchange = models.ForeignKey(Exchange, related_name='listed_exchange', on_delete=models.CASCADE, default=1)
    favourite = models.ManyToManyField(User, related_name='favourite_stock', blank=True)

    def __str__(self):
        return self.ticker

    def is_favourite(self, user):
        if self.favourite.filter(id=user.id).exists():
            return True
        return False

    def get_current_data(self):
        data = StockPriceData.objects.filter(stock=self).order_by('-timestamp')[:1]
        data = data.first()
        return data

    def get_currency(self):
        exchange = Exchange.objects.get(id=self.exchange.pk)
        country = Country.objects.get(id=exchange.country.pk)
        currency = Currency.objects.get(id=country.currency.pk)

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
        string = self.stock.ticker + ' ' + str(self.timestamp)
        return string

    class Meta:
        db_table = 'stock_price_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'stock']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['stock', 'timestamp'], name='unique_stock_data')
        ]


class FX(models.Model):
    code = models.CharField(max_length=10, unique=True)
    from_currency = models.ForeignKey(Currency, related_name='from_currency', on_delete=models.CASCADE, default=1)
    to_currency = models.ForeignKey(Currency, related_name='to_currency', on_delete=models.CASCADE, default='2')
    instrument = models.ForeignKey(Instrument, related_name='fx_instrument', default=1, on_delete=models.CASCADE)
    favourite_fx = models.ManyToManyField(User, related_name='favourite_fx', blank=True)

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

    def get_current_data(self):
        data = FXPriceData.objects.filter(stock=self).first()
        return data

    class Meta:
        db_table = 'fx_pair'
        indexes = [
            models.Index(fields=['from_currency', 'to_currency']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['from_currency', 'to_currency'], name='unique_currency_pair')
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
        constraints = [
            models.UniqueConstraint(fields=['currency_pair', 'timestamp'], name='unique_fx_data')
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
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    close_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    result = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    open = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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
        if self.open:
            if self.stock is None:
                fx = FX.objects.filter.get(id=self.fx.id)
                current_data = fx.get_current_data()
                self.result = current_data.close - self.open_price
                self.save()

            elif self.fx is None:
                stock = Stock.objects.get(id=self.stock.id)
                latest_price = stock.get_current_data()
                self.result = latest_price.close - self.open_price
                self.save()

            return self.result
        else:
            return self.result

    def result_change(self):
        if self.open:
            if self.stock is None:
                fx = FX.objects.filter.get(id=self.fx.id)
                current_data = fx.get_current_data()
                change = current_data.close - self.open_price
                print(change)
                return change

            elif self.fx is None:
                stock = Stock.objects.get(id=self.stock.id)
                latest_price = stock.get_current_data()
                change = latest_price.close - self.open_price
                return change
        else:
            return self.result

    def current_value(self):
        if self.stock is None:
            fx = FX.objects.filter.get(id=self.fx.id)
            current_data = fx.get_current_data()
            self.value = current_data.close * self.quantity
            self.save()

        elif self.fx is None:
            stock = Stock.objects.get(id=self.stock.id)
            latest_price = stock.get_current_data()
            self.value = latest_price.close * self.quantity
            self.save()

    class Meta:
        db_table = 'positions'




