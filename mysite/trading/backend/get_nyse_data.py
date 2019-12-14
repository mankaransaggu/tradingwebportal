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
from matplotlib import style
from pandas_datareader._utils import RemoteDataError
from .database import delete_stock, insert_stock, get_engine, create_df
from ..models import Stock, MarketData


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
            exchange = 'NYSE'
            print(ticker)

            try:
                insert_stock(name, ticker, exchange)
                get_nyse_data_yahoo(ticker)
                tickers.append(ticker)
                print('Added ', ticker)
            except (sqlalchemy.exc.IntegrityError, MySQLdb._exceptions.IntegrityError):
                message = 'Ticker {} already exsists in stock table'.format(ticker)

                try:
                    get_nyse_data_yahoo(ticker)
                    tickers.append(ticker)
                    print('Added {} data '.format(ticker))
                except RemoteDataError:
                    message = 'No data found for {}'.format(ticker)
                    stock = Stock.objects.get(ticker=ticker)
                    delete_stock(stock.pk)
                except (MySQLdb._exceptions.IntegrityError, sqlalchemy.exc.IntegrityError):
                    message = 'Market data for {} already up to date'.format(ticker)
                except KeyError:
                    message = 'Stock {} doesnt exist'.format(ticker)
                    delete_stock(stock.pk)

            except RemoteDataError:
                message = "No {} data on yahoo".format(ticker)
                delete_stock(stock.pk)
            except KeyError:
                message = 'Stock {} doesnt exist'.format(ticker)
                delete_stock(stock.pk)
            except:
                message = 'Unkown error with {}'.format(ticker)

    return tickers, message


def get_nyse_data_yahoo(ticker, reload_nyse=False):
    start = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')
    end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

    stock = Stock.objects.get(ticker=ticker)
    df = web.DataReader(ticker, 'yahoo', start, end)
    df = df.rename(columns={'High': 'high', 'Low': 'low', 'Open': 'open', 'Close': 'close', 'Volume': 'volume', 'Adj Close': 'adj_close'})
    df['ticker'] = stock.pk
    df.index.names = ['date']
    df.to_sql('market_data', get_engine(), if_exists='append', index=True)


def compile_nyse_data():
    with open('pickles/nysetickers.pickle', 'rb') as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()

    for count, ticker in enumerate(tickers):
        df = create_df(ticker)
        print(df.head())

        df.rename(columns={'adj_close': ticker}, inplace=True)
        df.drop(['ticker', 'open', 'high', 'low', 'close', 'volume'], 1, inplace=True)
        print(df.head())

        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')

        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('compiled_data/nyse_joined.csv')


def visualize_nyse_data():
    df = pd.read_csv('nyse_joined.csv')
    # df['AAPL'].plot()
    # plt.show()

    # This correleates the data
    df_corr = df.corr()
    print(df_corr)

    data = df_corr.values
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # This is building  the heat map, we take the colours RYG(Red, Yellow, Green)
    heatmap = ax.pcolor(data, cmap=plt.cm.RdYlGn)
    fig.colorbar(heatmap)
    #Every .5 there will be a tick
    ax.set_xticks(numpy.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_yticks(numpy.arange(data.shape[1]) + 0.5, minor=False)

    # This rotates the axis, the x is displayed at the top and the y on the side
    ax.invert_yaxis()
    ax.xaxis.tick_top()

    # Sets the row and column text
    column_labels = df_corr.columns
    row_labels = df_corr.index

    # Sets the graph labels and rotates the x axis 90
    ax.set_xticklabels(column_labels)
    ax.set_yticklabels(row_labels)
    plt.xticks(rotation=90)
    heatmap.set_clim(-1, 1)
    plt.tight_layout()
    plt.show()


def get_closest_to_dt(date):
    greater = MarketData.objects.filter(date__gte=date).order_by("date").first()
    less = MarketData.objects.filter(date__lte=date).order_by("-date").first()

    if greater and less:
        return greater if abs(greater.date - date) < abs(less.date - date) else less
    else:
        return greater or less
