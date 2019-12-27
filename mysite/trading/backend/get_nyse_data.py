import MySQLdb
import bs4 as bs
import pickle
import datetime as dt
import os
import pandas as pd
import pandas_datareader.data as web
import requests
import matplotlib.pyplot as plt
import numpy as numpy
import sqlalchemy
from django.db import IntegrityError
from matplotlib import style
from pandas_datareader._utils import RemoteDataError
from .database import delete_stock, insert_stock, get_engine, create_df
from ..models import Stock, MarketData, Exchange


style.use('ggplot')


def save_nyse_tickers():
    links = ("https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(0%E2%80%939)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(A)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(B)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(C)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(D)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(E)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(F)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(G)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(H)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(I)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(J)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(K)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(L)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(M)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(N)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(O)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(P)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(Q)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(R)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(S)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(T)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(U)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(V)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(W)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(X)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(Y)",
             "https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(Z)")

    tickers = []
    engine = get_engine()
    message = ''

    for link in links:
        resp = requests.get(link)
        soup = bs.BeautifulSoup(resp.text, "lxml")
        table = soup.findAll('table')[1]

        for row in table.findAll('tr')[1:]:
            ticker = row.findAll('td')[1].text
            ticker = ticker[:-1]
            mapping = str.maketrans(".", "-")
            ticker = ticker.translate(mapping)
            name = row.findAll('td')[0].text
            exchange = Exchange.objects.get(code='NYSE')

            try:
                stock = Stock.objects.update_or_create(ticker=ticker, name=name, exchange=exchange)
                success = True
                tickers.append(ticker)
                print('Added {} to stock table'.format(ticker))
            except IntegrityError:
                print('{} already exists in Stock table'.format(ticker))
                success = True

            if success:
                try:
                    stock = Stock.objects.get(ticker=ticker)
                    get_nyse_data_yahoo(ticker)
                except RemoteDataError:
                    print('No market data for {}'.format(ticker))
                    stock.delete()
                except IntegrityError:
                    print('Data for {} already exists'.format(ticker))
                except MySQLdb._exceptions.IntegrityError:
                    print('Data for {} already exists'.format(ticker))
                except sqlalchemy.exc.IntegrityError:
                    print('Data for {} already exists'.format(ticker))
                except KeyError:
                    print('No market data for {}'.format(ticker))
                    stock.delete()

    return tickers, message


def get_nyse_data_yahoo(ticker, reload_nyse=False):
    start = dt.datetime(2005, 1, 1)
    end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

    stock = Stock.objects.get(ticker=ticker)
    df = web.DataReader(ticker, 'yahoo', start, end)
    print('Before:')
    print(df.head())
    df = df.rename(columns={'High': 'high_price', 'Low': 'low_price', 'Open': 'open_price', 'Close': 'close_price',
                            'Volume': 'volume', 'Adj Close': 'adj_close'})
    df['ticker'] = stock.pk
    df.rename_axis('date', axis='index', inplace=True)
    print('after:')
    print(df.head())
    df.to_sql('market_data', get_engine(), if_exists='append', index=True)


def update_market_data():
    start = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')
    end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

    for stock in Stock.objects.all():
        try:
            ticker = stock.ticker
            stock = Stock.objects.get(ticker=ticker)
            df = web.DataReader(ticker, 'yahoo', start, end)
            df = df.rename(columns={'High': 'high_price', 'Low': 'low_price', 'Open': 'open_price', 'Close': 'close_price', 'Volume': 'volume',
                                    'Adj Close': 'adj_close'})
            df['ticker'] = stock.pk
            df.index.names = ['date']
            df.to_sql('market_data', get_engine(), if_exists='append', index=True)
            print('Recent data for {} added'.format(ticker))
        except:
            print('Cant update {}'.format(ticker))


def compile_nyse_data():
    with open('pickles/nysetickers.pickle', 'rb') as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()

    for count, ticker in enumerate(tickers):
        df = create_df(ticker)
        print(df.head())

        df.rename(columns={'adj_close': ticker}, inplace=True)
        df.drop(['ticker', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'], 1, inplace=True)
        print(df.head())

        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')

        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('compiled_data/nyse_joined.csv')
