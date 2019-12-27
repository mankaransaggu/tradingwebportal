import pandas as pd
from sqlalchemy import create_engine, insert, MetaData, Table, select, and_, delete, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists
from ..models import Stock, MarketData


def createmysqldb():
    engine = get_engine()
    engine = 'mysql://{0}:{1}@{2}:{3}/{4}'.format('stocks', 'Password10!', 'localhost', 3306, 'trading')

    if not database_exists(engine):
        create_database(engine)


# Returns engine for use in other areas without needing to the create_engine method
def get_engine():
    engine = create_engine('mysql://stocks:Password10!@localhost/trading')
    return engine


# Deletes stock from stock table of database
def delete_stock(stock):
    Stock.objects.filter(id=stock).delete()
    print('Deleted Stock {}'.format(stock))


# Inserts stock record into stock table of database
def insert_stock(name, ticker, exchange):
    engine = get_engine()
    metadata = MetaData(bind=engine)
    session = sessionmaker(bind=engine)()

    stock_table = Table('stock', metadata, autoload=True)
    stock = insert(stock_table)
    stock = stock.values({'name': name, 'ticker': ticker, 'exchange_id': exchange})

    session.execute(stock)
    session.commit()


# Gets all of the market data for the provided ticker
def get_stock_data(ticker):
    # Selects all records from market_data table where the ticker equals provided ticker
    stock = Stock.objects.get(ticker=ticker)
    print(stock.pk)
    engine = get_engine()
    metadata = MetaData(bind=engine)
    session = sessionmaker(bind=engine)()
    table = Table('market_data', metadata, autoload=True, autoload_with=engine)
    stmt = select([table]).where(and_(table.columns.ticker == stock.pk))

    fields = ['date', 'ticker', 'high_price', 'low_price', 'open_price', 'close_price', 'volume', 'adj_close']
    stocks = session.query()

    connection = engine.connect()
    results = connection.execute(stmt).fetchall()

    return results


def create_df(ticker):
    try:
        stock = Stock.objects.get(ticker=ticker)
        # SQL to read all the market data for specified stock and put into dataframe
        sql = 'SELECT date, high_price, low_price, open_price, close_price, volume, adj_close ' \
              'FROM market_data WHERE ticker = %s'
        df = pd.read_sql(sql, get_engine(), params={stock.pk})

        # Set the index of the dataframe as the date and make it datetime data so it can be used for resample
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)
        print(df.head())
        return df
    except:
        return 'No stock with provided ticker'


def get_stock_pk(ticker):
    stock = Stock.objects.get(ticker=ticker)

    return stock
