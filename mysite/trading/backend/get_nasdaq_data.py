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


def save_nasdaq_tickers():
    link = 'https://en.wikipedia.org/wiki/NASDAQ-100'

    tickers = []
    message = ''

    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.text, "lxml")
    table = soup.find('table', {'class': 'wikitable sortable'})

    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[1].text
        ticker = ticker[:-1]
        mapping = str.maketrans(".", "-")
        ticker = ticker.translate(mapping)
        name = row.findAll('td')[0].text
        exchange = Exchange.objects.get(code='NASDAQ')

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
                get_nasdaq_data_yahoo(ticker)
            except RemoteDataError:
                print('No market data for {}'.format(ticker))
                stock.delete()
            except IntegrityError:
                print('Data for {} already exists'.format(ticker))

    return tickers, message


def get_nasdaq_data_yahoo(ticker, reload_nasdaq=False):
    start = dt.datetime(2005, 1, 1)
    end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

    stock = Stock.objects.get(ticker=ticker)
    df = web.DataReader(ticker, 'yahoo', start, end)
    df = df.rename(columns={'High': 'high_price', 'Low': 'low_price', 'Open': 'open_price', 'Close': 'close_price',
                            'Volume': 'volume', 'Adj Close': 'adj_close'})
    df['ticker'] = stock.pk
    df.index.names = ['date']
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



