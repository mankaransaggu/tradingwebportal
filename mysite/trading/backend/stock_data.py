from plotly.subplots import make_subplots

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


def get_week(symbol):
    latest = get_yesterday(symbol)
    week = dt.datetime.strftime(latest.date - dt.timedelta(days=7), '%Y-%m-%d')
    res = get_closest_to_dt(week, symbol)
    week = res.date
    week = MarketData.objects.get(ticker__ticker=symbol, date=week)

    return week


# Gets the date closest to 365 days ago
def get_month(symbol):
    latest = get_yesterday(symbol)
    year = dt.datetime.strftime(latest.date - dt.timedelta(days=30), '%Y-%m-%d')
    res = get_closest_to_dt(year, symbol)
    month = res.date
    month = MarketData.objects.get(ticker__ticker=symbol, date=month)

    return month


# Gets the date closest to 365 days ago
def get_ytd(symbol):
    latest = get_yesterday(symbol)
    year = dt.datetime.strftime(latest.date - dt.timedelta(days=365), '%Y-%m-%d')
    res = get_closest_to_dt(year, symbol)
    ytd = res.date
    ytd = MarketData.objects.get(ticker__ticker=symbol, date=ytd)

    return ytd


def get_earliest(symbol):
    earliest = MarketData.objects.filter(ticker__ticker=symbol).order_by("date").first()

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


def create_stock_chart(days, instr, positions):
    df = stock_df(days, instr.ticker)
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
        width=2500,
        height=1000,
        autosize=True
    )

    for position in positions:
        print(position)
        fig.update_layout(
            shapes=[dict(
                y0=position.open_price, y1=position.open_price, x0=0, x1=1, yref='y', xref='paper',
                line_width=1)],
            annotations=[dict(
                y=position.open_price - 1, x=0.05, yref='y', xref='paper',
                showarrow=False, xanchor='left', text='Position Open')]
        )

    chart = opy.plot(fig, auto_open=False, output_type='div')

    return chart


def create_stock_change(instr):
    day_before = get_day_before(instr)
    yesterday = get_yesterday(instr)
    week = get_week(instr)
    month = get_month(instr)
    year = get_ytd(instr)
    all = get_earliest(instr)

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>1D Change</span>"},
        value=yesterday.close,
        domain={'x': [0, 0.25], 'y': [0, 0]},
        delta={'reference': day_before.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>7D Change</span>"},
        value=week.close,
        domain={'x': [0.25, 0.5], 'y': [0, 0]},
        delta={'reference': yesterday.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>30D Change</span>"},
        value=month.close,
        domain={'x': [0.5, 0.75], 'y': [0, 0]},
        delta={'reference': yesterday.close, 'relative': True}))

    fig.add_trace(go.Indicator(
        mode="number+delta",
        title={
            "text": "<span style='font-size:0.8em;color:gray'>YTD Change</span>"},
        value=year.close,
        domain={'x': [0.75, 1], 'y': [0, 0]},
        delta={'reference': yesterday.close, 'relative': True}))

    summary = opy.plot(fig, auto_open=False, output_type='div')
    return summary


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
    context['day_bef'] = get_day_before(symbol)
    context['week'] = get_week(symbol)
    context['month'] = get_month(symbol)
    context['ytd'] = get_ytd(symbol)
    context['earliest'] = get_earliest(symbol)

    context['yest_diff'] = get_change(context['latest'].close, context['day_bef'].close)
    context['yest_diff_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)
    context['yest_vol_diff'] = get_change_percent(context['latest'].volume, context['day_bef'].volume)

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
