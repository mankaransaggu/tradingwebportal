import MySQLdb
import requests
import sqlalchemy
from django.contrib import messages
from django.db import IntegrityError
from alpha_vantage.timeseries import TimeSeries
from ...models import StockPriceData, Stock
import pandas as pd
import datetime as dt
from django_pandas.io import read_frame


def stock_df(days, stock):
    try:
        date = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days), '%Y-%m-%d')
        qs = StockPriceData.objects.filter(stock_id=stock.pk, timestamp__gte=date)
        df = read_frame(qs)

        # Format df to have the correct columns and index
        del df['id']
        del df['stock']
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index)

        return df
    except TypeError:
        return None


def real_time_df(stock):

    try:
        stock = Stock.objects.get(id=stock.pk)
        ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
        df, meta_data = ts.get_intraday(symbol=stock.ticker, interval='1min', outputsize='full')

        df = df.rename(
            columns={'2. high': 'high', '3. low': 'low', '1. open': 'open', '4. close': 'close',
                     '5. volume': 'volume'})
        df['stock'] = stock
        df.rename_axis('timestamp', axis='index', inplace=True)
        df.index = pd.to_datetime(df.index)

        df_to_sql(df)
        return df

    except requests.exceptions.ConnectionError:
        return None
    except ValueError:
        return None


def df_to_sql(df):
    # Flip the data in the df, so it goes from latest to earliest data
    df = df.iloc[:-1]
    for row in df.itertuples():

        try:
            print(row)
            stock = getattr(row, 'stock')

            StockPriceData.objects.create(timestamp=getattr(row, 'Index'), high=getattr(row, 'high'),
                                          low=getattr(row, 'low'), open=getattr(row, 'open'),
                                          close=getattr(row, 'close'), volume=getattr(row, 'volume'),
                                          stock=getattr(row, 'stock'))

        except (IntegrityError, sqlalchemy.exc.IntegrityError, MySQLdb._exceptions.IntegrityError):
            print('Data {} already exists'.format(stock))
            break


