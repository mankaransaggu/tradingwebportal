import MySQLdb
import bs4 as bs
import datetime as dt
import pandas_datareader.data as web
import requests
import sqlalchemy
from alpha_vantage.timeseries import TimeSeries
from django.db import IntegrityError
from pandas_datareader._utils import RemoteDataError
from ..stock.stock_dataframes import df_to_sql
from ...models import Stock, Exchange, StockPriceData


class StockExchange:
    def ___init__(self, name, code, links, tickers, country):
        self.name = name
        self.code = code
        self.links = links
        self.ticker = tickers
        self.country = country

    def save_stocks(self):
        tickers = []

        for link in self.links:
            resp = requests.get(link)
            soup = bs.BeautifulSoup(resp.text, "lxml")
            table = soup.findAll('table')[1]

            for row in table.findAll('tr')[1:]:
                ticker = row.findAll('td')[1].text
                ticker = ticker[:-1]
                mapping = str.maketrans(".", "-")
                ticker = ticker.translate(mapping)
                name = row.findAll('td')[0].text
                exchange = Exchange.objects.get(code=self.code)

                try:
                    stock = Stock.objects.update_or_create(ticker=ticker, name=name, exchange=exchange)
                    success = True
                    stock = Stock.objects.get(ticker=ticker, exchange=exchange)
                    print('SUCCESS: Added {} to stock table'.format(ticker))
                except IntegrityError:
                    print('ERROR - IntegrityError: {} already exists in Stock table'.format(ticker))
                    success = True

                if success:
                    self.get_yahoo_data(stock)

        return tickers

    @staticmethod
    def get_yahoo_data(stock):
        try:
            start = dt.datetime(2017, 1, 1)
            end = dt.datetime.strftime(dt.datetime.now() - dt.timedelta(1), '%Y-%m-%d')

            df = web.DataReader(stock.ticker, 'yahoo', start, end)

            df = df.rename(
                columns={'High': 'high', 'Low': 'low', 'Open': 'open', 'Close': 'close',
                         'Volume': 'volume', 'Adj Close': 'adj_close'})
            df['stock'] = stock

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

    @staticmethod
    # This method uses the alpha vantage API, unfortunately not suitable for constant use due to api call limits
    def get_stock_data(stock):
        try:
            print(stock.pk)
            print(stock.ticker)
            ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
            df, meta_data = ts.get_daily_adjusted(symbol=stock.ticker, outputsize='full')

            df = df.rename(
                columns={'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close',
                         '5. adjusted close': 'adj_close', '6. volume': 'volume', '7. dividend amount': 'dividend',
                         '8. split coefficient': 'split_coefficient'})
            df['instrument_id'] = stock.pk
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

        except ValueError:
            print('ERROR - ValueError: No market data for {}'.format(stock.ticker))
            stock.delete()

    def update_market_data(self):
        end = dt.date.today() - dt.timedelta(1)

        for stock in Stock.objects.filter(exchange__code=self.code):

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


class NYSE(StockExchange):
    def __init__(self):
        self.name = 'New York Stock Exchange'
        self.code = 'NYSE'
        self.links = ("https://en.wikipedia.org/wiki/Companies_listed_on_the_New_York_Stock_Exchange_(0%E2%80%939)",
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


class NASDAQ(StockExchange):
    def __init__(self):
        self.name = 'Nasdaq'
        self.code = 'NASDAQ'
        self.links = ('https://www.advfn.com/nasdaq/nasdaq.asp?companies=A',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=B',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=C',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=D',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=E',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=F',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=G',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=H',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=I',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=J',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=K',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=L',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=M',)
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=N',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=O',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=P',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Q',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=R',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=S',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=T',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=U',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=V',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=W',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=X',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Y',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Z',
                      # 'https://www.advfn.com/nasdaq/nasdaq.asp?companies=0',)

    # Currently have to override parent due to different elements, looking to solve
    def save_stocks(self):
        tickers = []

        for link in self.links:
            resp = requests.get(link)
            soup = bs.BeautifulSoup(resp.text, "lxml")
            table = soup.find('table', {'class': 'market tab1'})

            for row in table.findAll('tr')[2:]:
                ticker = row.findAll('td')[1].text
                mapping = str.maketrans(".", "-")
                ticker = ticker.translate(mapping)
                name = row.findAll('td')[0].text
                exchange = Exchange.objects.get(code='NASDAQ')

                try:
                    Stock.objects.update_or_create(ticker=ticker, name=name, exchange=exchange)
                    print('Added {} to stock table'.format(ticker))
                    success = True
                except IntegrityError:
                    print('{} already exists in Stock table'.format(ticker))
                    success = True

                if success:
                    stock = Stock.objects.get(ticker=ticker, exchange=exchange)
                    self.get_yahoo_data(stock)

        return tickers
