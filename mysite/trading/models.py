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
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.code

    def get_pairs(self):
        print(FX.objects.filter(from_currency=self) | FX.objects.filter(to_currency=self))
        return FX.objects.filter(from_currency=self) | FX.objects.filter(to_currency=self)

    class Meta:
        db_table = 'currency'
        constraints = [
            models.UniqueConstraint(fields=['code', 'name'], name='currency')
        ]


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
    funds = models.DecimalField('account_funds', blank=False, null=False, decimal_places=2, max_digits=12, default=0)

    result = models.DecimalField('account_result', blank=True, null=False, decimal_places=2, max_digits=12, default=0)
    live_result = models.DecimalField('live_result', blank=False, null=False, decimal_places=2, max_digits=12,
                                      default=0)

    is_verified = models.BooleanField('verified', default=False)
    verification_uuid = models.UUIDField('Unique Verification UUID', default=uuid.uuid4)

    is_staff = models.BooleanField('staff_status', default=False)
    is_active = models.BooleanField('active', default=True)
    date_joined = models.DateTimeField('date_joined', default=django.utils.timezone.now)
    last_login = models.DateTimeField('last_login', default=django.utils.timezone.now)

    base_currency = models.ForeignKey(Currency, related_name='base_currency', blank=False, null=False,
                                      on_delete=models.CASCADE)

    def __unicode__(self):
        return self.email

    def get_live_result(self):
        open_positions = Position.objects.filter(user=self, open=True)
        self.live_result = 0

        for pos in open_positions:
            currency = pos.instrument.exchange.get_currency()
            fx = FX.objects.get(from_currency=currency, to_currency=self.base_currency)
            rate = FXPriceData.objects.filter(currency_pair=fx).order_by('-timestamp').first()

            self.live_result += pos.get_current_data().result * rate.close
            self.save()

        return round(self.live_result, 2)

    def get_account_value(self):
        open_positions = Position.objects.filter(user=self, open=True)
        account_value = 0
        for position in open_positions:
            currency = position.instrument.exchange.get_currency()
            fx = FX.objects.get(from_currency=currency, to_currency=self.base_currency)
            rate = FXPriceData.objects.filter(currency_pair=fx).order_by('-timestamp').first()
            account_value += position.value * rate.close

        self.value = self.funds + account_value
        self.save()

        return round(self.value, 2)


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
        country = Country.objects.get(code=self.country)
        currency = Currency.objects.get(code=country.currency)
        return currency

    def get_stock_count(self):
        return self.listed_exchange.count()

    def get_listed_stocks(self):
        return self.listed_exchange.all()

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
        constraints = [
            models.UniqueConstraint(fields=['code', 'name'], name='instrument_type')
        ]


class DataType(models.Model):
    code = models.CharField(max_length=25, unique=True, blank=False, null=False)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'data_types'


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

    def get_change(self):
        latest = StockPriceData.objects.filter(stock=self).order_by('-timestamp')

        if not latest:
            return None
        latest = latest.first()

        if latest.data_type.code == 'INTRADAY':
            previous = StockPriceData.objects.filter(stock=self, data_type__code='DAILY').order_by('-timestamp')[1]
        else:
            try:
                previous = StockPriceData.objects.filter(stock=self, data_type__code='DAILY').order_by('-timestamp')[2]
            except IndexError:
                return None

        return latest.close - previous.close

    def get_change_perc(self):
        latest = StockPriceData.objects.filter(stock=self).order_by('-timestamp')

        if not latest:
            return None
        latest = latest.first()

        if latest.data_type.code == 'INTRADAY':
            previous = StockPriceData.objects.filter(stock=self, data_type__code='DAILY').order_by('-timestamp')[1]
        else:
            try:
                previous = StockPriceData.objects.filter(stock=self, data_type__code='DAILY').order_by('-timestamp')[2]
            except IndexError:
                return None

        if latest.close == previous.close:
            return 0

        try:
            percent = (abs(latest.close - previous.close) / previous.close) * 100
            percent = round(percent, 2)
            return percent

        except ZeroDivisionError:
            return 0

    def get_currency(self):
        exchange = Exchange.objects.get(id=self.exchange.pk)
        country = Country.objects.get(id=exchange.country.pk)
        currency = Currency.objects.get(id=country.currency.pk)
        return currency

    class Meta:
        db_table = 'stock'
        constraints = [
            models.UniqueConstraint(fields=['ticker', 'name', 'exchange_id'], name='company_stock')
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

    data_type = models.ForeignKey(DataType, null=False, blank=False, on_delete=models.CASCADE)

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

    def is_favourite(self, user):
        if self.favourite.filter(id=user.id).exists():
            return True

        return False

    def get_current_data(self):
        data = FXPriceData.objects.filter(currency_pair=self).first()
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
    high = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal(0.00))
    low = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal(0.00))
    open = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal(0.00))
    close = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal(0.00))
    volume = models.IntegerField(blank=True, null=True)

    data_type = models.ForeignKey(DataType, default=1, null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        string = self.currency_pair.code + ' ' + str(self.timestamp)
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

    def get_current_data(self):
        if self.stock is None:
            fx = FX.objects.filter.get(id=self.fx.id)
            latest_data = fx.get_current_data()
            self.value = latest_data.close * self.quantity
            self.result = latest_data.close - self.open_price
            self.save()

        elif self.fx is None:
            stock = Stock.objects.get(id=self.stock.id)
            latest_data = stock.get_current_data()
            self.value = latest_data.close * self.quantity
            self.result = latest_data.close - self.open_price
            self.save()

        return self

    def get_user_currency(self):
        self.get_current_data()

        user = User.objects.get(id=self.user.pk)
        user_currency = user.base_currency
        instrument_curreny = self.stock.get_currency()
        fx = FX.objects.get(from_currency=instrument_curreny.pk, to_currency=user_currency.pk)
        rate = FXPriceData.objects.filter(currency_pair=fx).order_by('-timestamp')
        rate = rate.first()

        converted = Position
        converted.value = round(self.value * rate.close, 2)
        converted.open_price = round(self.open_price * rate.close, 2)
        converted.close_price = round(self.close_price * rate.close, 2)
        converted.current_price = round(self.stock.get_current_data().close * rate.close, 2)
        converted.result = round(self.result * rate.close, 2)
        return converted

    class Meta:
        db_table = 'positions'
