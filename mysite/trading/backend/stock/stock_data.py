import MySQLdb
import sqlalchemy
from alpha_vantage.timeseries import TimeSeries
from django.db import IntegrityError
from pandas_datareader._utils import RemoteDataError
from ...models import Stock, StockPriceData, DataType
from .stock_dataframes import df_to_sql
import datetime as dt
import pandas_datareader.data as web


def get_yahoo_data(stock):
    try:
        start = dt.datetime(2017, 1, 1)
        end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

        df = web.DataReader(stock.ticker, 'yahoo', start, end)

        df = df.rename(
            columns={'High': 'high', 'Low': 'low', 'Open': 'open', 'Close': 'close',
                     'Volume': 'volume', 'Adj Close': 'adj_close'})
        df['stock'] = stock

        df['data_type'] = DataType.objects.get(code='DAILY')

        df.rename_axis('timestamp', axis='index', inplace=True)
        df_to_sql(df)

        print('SUCCESS: Market data for {} added'.format(stock.ticker))

    except RemoteDataError:
        print('ERROR - RemoteDataError: No market data for {}'.format(stock.ticker))
        stock.delete()

    except (IntegrityError, MySQLdb._exceptions.IntegrityError, sqlalchemy.exc.IntegrityError) as e:
        print('ERROR - IntegrityError: Data for {} already exists'.format(stock.ticker))

    except KeyError:
        print('ERROR - KeyError: No market data for {}'.format(stock.ticker))
        stock.delete()

    except AssertionError:
        print('ERROR - AssertionError: Stock {} should be deleted'.format(stock.ticker))


# This method uses the alpha vantage API, unfortunately not suitable for constant use due to api call limits
def get_stock_data(stock):
    try:
        ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
        df, meta_data = ts.get_daily_adjusted(symbol=stock.ticker, outputsize='full')

        df = df.rename(
            columns={'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close',
                     '5. adjusted close': 'adj_close', '6. volume': 'volume', '7. dividend amount': 'dividend',
                     '8. split coefficient': 'split_coefficient'})
        df['instrument_id'] = stock.pk
        df['data_type'] = DataType.objects.get(code='INTRADAY')
        df.rename_axis('timestamp', axis='index', inplace=True)

        df_to_sql(df)
        print('SUCCESS: Market data for {} added'.format(stock.ticker))

    except RemoteDataError:
        print('ERROR - RemoteDataError: No market data for {}'.format(stock.ticker))
        stock.delete()


def update_market_data():
    end = dt.date.today() - dt.timedelta(1)

    for stock in Stock.objects.all():

        latest = StockPriceData.objects.filter(instrument=stock).order_by('-timestamp')[:1]
        if latest.exists():
            latest = latest.first()
            start = latest.timestamp.date() + dt.timedelta(1)

            if start < end:

                try:
                    ticker = stock.ticker
                    df = web.DataReader(ticker, 'yahoo', start, end)
                    # Format df ready for insertion to db
                    df = df.rename(
                        columns={'High': 'high', 'Low': 'low', 'Open': 'open', 'Close': 'close',
                                 'Volume': 'volume', 'Adj Close': 'adj_close'})
                    df['instrument_id'] = stock.pk
                    df['data_type'] = DataType.objects.get(code='DAILY')
                    df.index.names = ['timestamp']

                    df_to_sql(df)
                    print('Recent data for {} added'.format(ticker))

                except RemoteDataError:
                    print('No new market data for {}'.format(ticker))
                    stock.delete()

                except (IntegrityError, MySQLdb._exceptions.IntegrityError, sqlalchemy.exc.IntegrityError,) as e:
                    print('Recent data for {} already exists'.format(ticker))

                except KeyError:
                    print('No market data for {}'.format(ticker))
                    stock.delete()
