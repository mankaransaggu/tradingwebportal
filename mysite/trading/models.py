from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


DIRECTION_CHOICES = [
    ('BUY', 'BUY'),
    ('SELL', 'SELL'),
]

POSITION_STATES = [
    ('Open', 'Open'),
    ('Closed', 'Closed'),
]


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

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

    def __str__(self):
        return self.ticker

    class Meta:
        db_table = 'stock'


class MarketData(models.Model):
    date = models.DateField()
    ticker = models.ForeignKey(Stock, on_delete=models.CASCADE, db_column='ticker')
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    open = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    adj_close = models.FloatField(blank=True, null=True)

    def __str__(self):
        string = self.ticker.ticker + ' ' + self.date.strftime('%Y-%m-%d')
        return string

    class Meta:
        db_table = 'market_data'
        unique_together = (('date', 'ticker'),)


class Position(models.Model):
    position_number = models.AutoField(primary_key=True)
    ticker = models.ForeignKey(Stock, on_delete=models.CASCADE)
    open_date = models.DateField(default=None, blank=True, null=True)
    close_date = models.DateField(default=None, blank=True, null=True)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    quantity = models.FloatField()
    open_price = models.FloatField()
    close_price = models.FloatField(default=None, blank=True, null=True)
    result = models.FloatField(default=None, blank=True, null=True)
    position_state = models.CharField(max_length=10, choices=POSITION_STATES)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.position_number)

    class Meta:
        db_table = 'positions'


class Favourites(models.Model):
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def __str__(self):
        string = self.stock.ticker + ' ' + self.account.email
        return string

    class Meta:
        db_table = 'favourites'
        unique_together = (('account', 'stock'),)
