import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.offline as opy
from django_pandas.io import read_frame

from ..stock.stock_dataframes import stock_df, real_time_df
from ..stock.stock_dates import *


def create_stock_chart(days, stock):

    df = stock_df(days, stock)
    print(df)
    if not df.empty:
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
    else:
        return 'No historical data stored'


def create_intraday_chart(stock):

    try:
        if real_time_df(stock) is None:
            yest = get_yesterday(stock)
            qs = StockPriceData.objects.filter(stock=stock, timestamp__gte=yest.timestamp)
            df = read_frame(qs)
        else:
            df = real_time_df(stock)

        print(df)

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

    except TypeError:
        return None


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


