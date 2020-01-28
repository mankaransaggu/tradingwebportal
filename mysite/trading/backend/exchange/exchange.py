import bs4 as bs
import requests
from django.db import IntegrityError
from ...models import Stock, Exchange, StockPriceData
from ..stock.stock_data import get_yahoo_data


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
                    get_yahoo_data(stock)

        return tickers


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
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=M',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=N',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=O',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=P',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Q',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=R',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=S',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=T',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=U',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=V',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=W',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=X',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Y',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=Z',
                      'https://www.advfn.com/nasdaq/nasdaq.asp?companies=0',)

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
                    if stock.ticker == 'AAPL':
                        print('THIS IS APPLE WORK BUM')
                    get_yahoo_data(stock)

        return tickers
