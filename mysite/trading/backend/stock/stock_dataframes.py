import MySQLdb
import sqlalchemy
from django.db import IntegrityError
from alpha_vantage.timeseries import TimeSeries
from ...models import StockPriceData, Stock
import pandas as pd
import datetime as dt
from django_pandas.io import read_frame


def stock_df(days, stock):
    try:
        print(stock)
        print(type(stock))
        date = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(days), '%Y-%m-%d')
        qs = StockPriceData.objects.filter(stock_id=stock.pk, timestamp__gte=date)
        df = read_frame(qs)
        print(df)
        del df['id']
        del df['stock']
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index)
        print(df)
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


def df_to_sql(df):
    for index, row in df.iterrows():

        try:
            timestamp = index
            high = row['high']
            low = row['low']
            open = row['open']
            close = row['close']
            volume = row['volume']
            stock = row['stock']

            StockPriceData.objects.update_or_create(timestamp=timestamp, high=high, low=low, open=open, close=close,
                                                    volume=volume, stock=stock)

        except IntegrityError:
            print('Data {} already exists'.format(row['stock']))
            break

        except MySQLdb._exceptions.IntegrityError:
            print('Data {} already exists'.format(row['stock']))
            break

        except sqlalchemy.exc.IntegrityError:
            print('Data {} already exists'.format(row['stock']))
            break

