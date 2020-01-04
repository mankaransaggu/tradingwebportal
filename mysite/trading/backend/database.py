import MySQLdb
import pandas as pd
import sqlalchemy
from django.db import IntegrityError
from sqlalchemy import create_engine, insert, MetaData, Table, select, and_, delete, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists
from ..models import Stock, StockData, IntradayData


def createmysqldb():
    engine = get_engine()
    engine = 'mysql://{0}:{1}@{2}:{3}/{4}'.format('stocks', 'Password10!', 'localhost', 3306, 'trading')

    if not database_exists(engine):
        create_database(engine)


# Returns engine for use in other areas without needing to the create_engine method
def get_engine():
    engine = create_engine('mysql://stocks:Password10!@localhost/trading')
    return engine


# Gets all of the market data for the provided ticker
def get_stock_data(ticker):
    # Selects all records from market_data table where the ticker equals provided ticker
    stock = Stock.objects.get(ticker=ticker)
    print(stock.pk)
    engine = get_engine()
    metadata = MetaData(bind=engine)
    table = Table('stock_data', metadata, autoload=True, autoload_with=engine)
    stmt = select([table]).where(and_(table.columns.instrument_id == stock.pk))

    connection = engine.connect()
    results = connection.execute(stmt).fetchall()

    return results


# Old method using raw sql, can now use django ORM
def create_df(ticker):
    try:
        stock = Stock.objects.get(ticker=ticker)
        # SQL to read all the market data for specified stock and put into dataframe
        sql = 'SELECT date, high, low, open, close, volume, adj_close ' \
              'FROM stock_data WHERE ticker = %s'
        df = pd.read_sql(sql, get_engine(), params={stock.pk})

        # Set the index of the dataframe as the date and make it datetime data so it can be used for resample
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)

        return df

    except:
        return 'No stock with provided ticker'


def get_stock_pk(ticker):
    stock = Stock.objects.get(ticker=ticker)

    return stock


def df_to_sql(df):
    for index, row in df.iterrows():

        try:
            timestamp = index
            high = row['high']
            low = row['low']
            open = row['open']
            close = row['close']
            volume = row['volume']
            instrument = row['instrument_id']

            data = IntradayData.objects.update_or_create(timestamp=timestamp, high=high, low=low, open=open,
                                                         close=close, volume=volume, instrument_id=instrument)


        except IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break

        except MySQLdb._exceptions.IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break

        except sqlalchemy.exc.IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break