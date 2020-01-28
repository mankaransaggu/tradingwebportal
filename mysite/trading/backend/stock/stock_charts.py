import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.offline as opy
from django_pandas.io import read_frame

from ..stock.stock_dataframes import get_stock_df, get_real_time_df
from ..stock.stock_dates import *


def create_stock_chart(days, stock):

    df = get_stock_df(days, stock)

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

        df = get_real_time_df(stock)
        if not df.empty:

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
        else:
            print('Cant retrieve intraday data')

    except TypeError:
        return None

