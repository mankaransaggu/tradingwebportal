from ..models import MarketData
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
import datetime as dt
from django_pandas.io import read_frame


# Gets the change between two dates data in percent
def get_change_percent(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0


# Gets the change between two dates data
def get_change(current, previous):
    return current - previous


# Gets yesterday or latest day
def get_yesterday(symbol):
    yesterday = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    result = get_closest_to_dt(yesterday, symbol)
    nearest_yesterday = result.date
    latest = MarketData.objects.get(ticker__ticker=symbol, date=nearest_yesterday)

    return latest


# Gets the date closest to 365 days ago
def get_ytd(symbol):
    year = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=365), '%Y-%m-%d')
    res = get_closest_to_dt(year, symbol)
    ytd = res.date
    ytd = MarketData.objects.get(ticker__ticker=symbol, date=ytd)

    return ytd


def get_earliest(symbol):
    res = get_earliest_date(symbol)
    earliest = res.date
    earliest = MarketData.objects.get(ticker__ticker=symbol, date=earliest)

    return earliest


# Gets the second business day past
def get_day_before(symbol):
    day_before = MarketData.objects.filter(ticker__ticker=symbol).order_by('-date')[1]

    return day_before


# Gets the closest date to the given date
def get_closest_to_dt(date, symbol):
    greater = MarketData.objects.filter(date__gte=date, ticker__ticker=symbol).order_by("date").first()
    less = MarketData.objects.filter(date__lte=date, ticker__ticker=symbol).order_by("-date").first()
    date_obj = dt.datetime.strptime(date, '%Y-%m-%d').date()

    if greater and less:
        return greater if abs(greater.date - date_obj) < abs(less.date - date_obj) else less
    else:
        return greater or less


# Gets the earliest date avaliable
def get_earliest_date(symbol):
    earliest = MarketData.objects.filter(ticker__ticker=symbol).order_by("date").first()
    return earliest


def create_stock_chart(days,  symbol):
    df = stock_df(days, symbol)

    # Create the two
    df_ohlc = df['adj_close'].resample('10D').ohlc()

    df_ohlc.reset_index(inplace=True)
    df_ohlc['date'] = df_ohlc['date'].map(mdates.date2num)

    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['open'],
                                         high=df['high'],
                                         low=df['low'],
                                         close=df['close']
                                         )])
    fig.update_layout(
        title=symbol + ' Market Chart',
        yaxis_title='Price $',
        width=2500,
        height=1000,
        autosize=True
    )

    div = opy.plot(fig, auto_open=False, output_type='div')

    return div


def stock_df(days, ticker):
    try:
        date = end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days), '%Y-%m-%d')
        qs = MarketData.objects.filter(ticker__ticker=ticker, date__gte=date)
        df = read_frame(qs)
        del df['id']
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)

        return df

    except:
        return 'No stock with provided ticker'


def get_view_context(context, symbol):
    context['latest'] = get_yesterday(symbol)
    context['ytd'] = get_ytd(symbol)
    context['day_bef'] = get_day_before(symbol)
    context['earliest'] = get_earliest(symbol)

    context['yest_diff'] = get_change(context['latest'].close, context['day_bef'].close)
    context['yest_diff_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)
    context['yest_vol_diff'] = get_change_percent(context['latest'].volume, context['day_bef'].volume)

    context['ytd_diff_perc'] = get_change_percent(context['latest'].close, context['ytd'].close)
    context['ytd_diff'] = get_change(context['latest'].close, context['ytd'].close)
    context['ytd_vol_diff'] = get_change_percent(context['latest'].volume, context['ytd'].volume)

    context['early_diff'] = get_change(context['latest'].close, context['earliest'].close)
    context['early_diff_perc'] = get_change_percent(context['latest'].close, context['earliest'].close)
    context['early_vol_diff'] = get_change_percent(context['latest'].volume, context['earliest'].volume)

    return context