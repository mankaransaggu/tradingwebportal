from django.utils import timezone

from ...models import StockPriceData
import datetime as dt


def get_latest(stock):

    try:
        latest = StockPriceData.objects.filter(stock=stock).order_by('-timestamp').first()
    except StockPriceData.DoesNotExist:
        latest - StockPriceData.objects.filter(stock=stock).order_by('-timestamp').first()

    return latest


# Gets yesterday or latest day
def get_yesterday(stock):
    yesterday = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    result = get_closest_to_dt(yesterday, stock)
    nearest_yesterday = result.timestamp
    latest = StockPriceData.objects.get(stock=stock, timestamp=nearest_yesterday)

    return latest


def get_week(stock):
    latest = get_yesterday(stock)
    week = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=7), '%Y-%m-%d')
    res = get_closest_to_dt(week, stock)
    week = res.timestamp
    week = StockPriceData.objects.get(stock=stock, timestamp=week)

    return week


# Gets the date closest to 365 days ago
def get_month(stock):
    latest = get_yesterday(stock)
    year = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=30), '%Y-%m-%d')
    res = get_closest_to_dt(year, stock)
    month = res.timestamp
    month = StockPriceData.objects.get(stock=stock, timestamp=month)

    return month


# Gets the date closest to 365 days ago
def get_ytd(stock):
    latest = get_yesterday(stock)
    year = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=365), '%Y-%m-%d')
    res = get_closest_to_dt(year, stock)
    ytd = res.timestamp
    ytd = StockPriceData.objects.get(stock=stock, timestamp=ytd)

    return ytd


def get_earliest(stock):
    earliest = StockPriceData.objects.filter(stock=stock).order_by("timestamp").first()

    return earliest


# Gets the second business day past
def get_day_before(stock):
    day_before = StockPriceData.objects.filter(stock=stock).order_by('-timestamp')[1]
    return day_before


# Gets the closest date to the given date
def get_closest_to_dt(date, stock):
    greater = StockPriceData.objects.filter(timestamp__gte=date, stock=stock).order_by("timestamp").first()
    less = StockPriceData.objects.filter(timestamp__lte=date, stock=stock).order_by("-timestamp").first()
    date_obj = timezone.now()

    if greater and less:
        return greater if abs(greater.timestamp - date_obj) < abs(less.timestamp - date_obj) else less
    else:
        return greater or less
