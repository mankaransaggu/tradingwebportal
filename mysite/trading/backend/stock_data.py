from alpha_vantage.timeseries import TimeSeries
from .database import df_to_sql
from ..models import StockData, Stock, IntradayData
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
import datetime as dt
from django_pandas.io import read_frame
from django.utils import timezone


# Gets the change between two dates data in percent
def get_change_percent(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100
    except ZeroDivisionError:
        return 0


# Gets the change between two dates data
def get_change(current, previous):
    return current - previous


def get_latest(stock):

    try:
        latest = IntradayData.objects.filter(instrument=stock).order_by('-timestamp').first()
    except IntradayData.DoesNotExist:
        latest - StockData.objects.filter(instrument=stock).order_by('-timestamp').first()

    return latest


# Gets yesterday or latest day
def get_yesterday(stock):
    yesterday = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days=1), '%Y-%m-%d')
    result = get_closest_to_dt(yesterday, stock)
    nearest_yesterday = result.timestamp
    latest = StockData.objects.get(instrument=stock, timestamp=nearest_yesterday)

    return latest


def get_week(stock):
    latest = get_yesterday(stock)
    week = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=7), '%Y-%m-%d')
    res = get_closest_to_dt(week, stock)
    week = res.timestamp
    week = StockData.objects.get(instrument=stock, timestamp=week)

    return week


# Gets the date closest to 365 days ago
def get_month(stock):
    latest = get_yesterday(stock)
    year = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=30), '%Y-%m-%d')
    res = get_closest_to_dt(year, stock)
    month = res.timestamp
    month = StockData.objects.get(instrument=stock, timestamp=month)

    return month


# Gets the date closest to 365 days ago
def get_ytd(stock):
    latest = get_yesterday(stock)
    year = dt.datetime.strftime(latest.timestamp - dt.timedelta(days=365), '%Y-%m-%d')
    res = get_closest_to_dt(year, stock)
    ytd = res.timestamp
    ytd = StockData.objects.get(instrument=stock, timestamp=ytd)

    return ytd


def get_earliest(stock):
    earliest = StockData.objects.filter(instrument=stock).order_by("timestamp").first()

    return earliest


# Gets the second business day past
def get_day_before(stock):
    day_before = StockData.objects.filter(instrument=stock).order_by('-timestamp')[1]
    return day_before


# Gets the closest date to the given date
def get_closest_to_dt(date, stock):
    greater = StockData.objects.filter(timestamp__gte=date, instrument__ticker=stock).order_by("timestamp").first()
    less = StockData.objects.filter(timestamp__lte=date, instrument__ticker=stock).order_by("-timestamp").first()
    date_obj = timezone.now()

    if greater and less:
        return greater if abs(greater.timestamp - date_obj) < abs(less.timestamp - date_obj) else less
    else:
        return greater or less


def create_stock_chart(days, stock):
    df = stock_df(days, stock)
    df['adj_close'] = df['adj_close'].apply(float)
    df_ohlc = df['adj_close'].resample('10D').ohlc()
    df_ohlc.reset_index(inplace=True)
    df_ohlc['timestamp'] = df_ohlc['timestamp'].map(mdates.date2num)

    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['open'],
                                         high=df['high'],
                                         low=df['low'],
                                         close=df['close']
                                         )])

    fig.update_layout(
        xaxis=go.layout.XAxis(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")

                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    fig.update_layout(
        yaxis_title='Price $',
        width=2450,
        height=1000,
        autosize=True
    )

    chart = opy.plot(fig, auto_open=False, output_type='div')

    return chart


def create_intraday_chart(stock):
    df = real_time_df(stock)
    df['close'] = df['close'].apply(float)
    df_ohlc = df['close'].resample('1m').ohlc()
    df_ohlc.reset_index(inplace=True)
    df_ohlc['timestamp'] = df_ohlc['timestamp'].map(mdates.date2num)

    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['open'],
                                         high=df['high'],
                                         low=df['low'],
                                         close=df['close'])])

    fig.update_layout(
        yaxis_title='Price $',
        width=2450,
        height=1000,
        autosize=True
    )

    chart = opy.plot(fig, auto_open=False, output_type='div')

    return chart


def create_stock_change(stock):
    day_before = get_day_before(stock)
    yesterday = get_yesterday(stock)
    week = get_week(stock)
    month = get_month(stock)
    year = get_ytd(stock)

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>1D Close Change</span>"},
        value=yesterday.close,
        domain={'x': [0, 0.25], 'y': [0, 0]},
        delta={'reference': day_before.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>7D Close Change</span>"},
        value=yesterday.close,
        domain={'x': [0.25, 0.5], 'y': [0, 0]},
        delta={'reference': week.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>30D Close Change</span>"},
        value=month.close,
        domain={'x': [0.5, 0.75], 'y': [0, 0]},
        delta={'reference': yesterday.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>YTD Close Change</span>"},
        value=yesterday.close,
        domain={'x': [0.75, 1], 'y': [0, 0]},
        delta={'reference': year.close, 'relative': True}))

    summary = opy.plot(fig, auto_open=False, output_type='div')
    return summary


def stock_df(days, stock):
    try:
        date = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days), '%Y-%m-%d')
        qs = StockData.objects.filter(instrument=stock, timestamp__gte=date)
        df = read_frame(qs)
        del df['id']
        del df['instrument']
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index)

        return df

    except:
        return print('No stock with provided ticker')


def real_time_df(stock):
    stock = Stock.objects.get(id=stock.pk)
    ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
    df, meta_data = ts.get_intraday(symbol=stock.ticker, interval='1min', outputsize='full')

    df = df.rename(
        columns={'2. high': 'high', '3. low': 'low', '1. open': 'open', '4. close': 'close',
                 '5. volume': 'volume'})
    df['instrument_id'] = stock.pk
    df.rename_axis('timestamp', axis='index', inplace=True)

    df_to_sql(df)

    return df


def get_view_context(context):

    context['day_change'] = get_change(context['latest'].close, context['day_bef'].close)
    context['day_change_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)

    context['yest_diff'] = get_change(context['latest'].close, context['day_bef'].close)
    context['yest_diff_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)
    context['yest_vol_diff'] = get_change_percent(context['yesterday'].volume, context['day_bef'].volume)

    context['week_diff'] = get_change(context['latest'].close, context['week'].close)
    context['week_diff_perc'] = get_change_percent(context['latest'].close, context['week'].close)
    context['week_vol_diff'] = get_change_percent(context['latest'].volume, context['week'].volume)

    context['month_diff'] = get_change(context['latest'].close, context['month'].close)
    context['month_diff_perc'] = get_change_percent(context['latest'].close, context['month'].close)
    context['month_vol_diff'] = get_change_percent(context['latest'].volume, context['month'].volume)

    context['ytd_diff_perc'] = get_change_percent(context['latest'].close, context['ytd'].close)
    context['ytd_diff'] = get_change(context['latest'].close, context['ytd'].close)
    context['ytd_vol_diff'] = get_change_percent(context['latest'].volume, context['ytd'].volume)

    context['early_diff'] = get_change(context['latest'].close, context['earliest'].close)
    context['early_diff_perc'] = get_change_percent(context['latest'].close, context['earliest'].close)
    context['early_vol_diff'] = get_change_percent(context['latest'].volume, context['earliest'].volume)

    return context


def create_detail_data(stock, context):
    context['historic_graph'] = create_stock_chart(365, stock)
    context['intraday_graph'] = create_intraday_chart(stock)

    context['latest'] = get_latest(stock)
    context['yesterday'] = get_yesterday(stock)
    context['day_bef'] = get_day_before(stock)
    context['week'] = get_week(stock)
    context['month'] = get_month(stock)
    context['ytd'] = get_ytd(stock)
    context['earliest'] = get_earliest(stock)

    get_view_context(context)

    context['summary'] = create_stock_change(stock)


def get_latest_stock_details(context):
    stocks = Stock.objects.all().only('id')
    details = get_latest(stocks)

    context['stock_details'] = details
