from ..models import MarketData
from . import get_nyse_data as nyse_data
import datetime as dt


def get_change_percent(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0


def get_change(current, previous):
    return current - previous


def get_yesterday(symbol):
    yesterday = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    res = get_closest_to_dt(yesterday, symbol)
    nearest_yesterday = res.date

    latest = MarketData.objects.get(ticker__ticker=symbol, date=nearest_yesterday)

    return latest


def get_day_before(symbol):
    yesterday = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    res = get_day_before(yesterday, symbol)
    print(res)
    nearest_yesterday = res.date

    latest = MarketData.objects.get(ticker__ticker=symbol, date=nearest_yesterday)

    return latest


def get_ytd(symbol):
    year = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=365), '%Y-%m-%d')
    res = get_closest_to_dt(year, symbol)
    ytd = res.date

    ytd = MarketData.objects.get(ticker__ticker=symbol, date=ytd)

    return ytd


def get_closest_to_dt(date, symbol):
    greater = MarketData.objects.filter(date__gte=date, ticker__ticker=symbol).order_by("date").first()
    less = MarketData.objects.filter(date__lte=date, ticker__ticker=symbol).order_by("-date").first()
    print(greater)
    print(less)
    if greater and less:
        return greater if abs(greater.date - date) < abs(less.date - date) else less
    else:
        return greater or less


def get_day_before(date, symbol):
    greater = MarketData.objects.filter(date__gte=date, ticker__ticker=symbol).order_by("date")[1:1]
    less = MarketData.objects.filter(date__lte=date, ticker__ticker=symbol).order_by("-date")[1:1]
    print(greater)
    print(less)
    if greater and less:
        return greater if abs(greater.date - date) < abs(less.date - date) else less
    else:
        return greater or less
