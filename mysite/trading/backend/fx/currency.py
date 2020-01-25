import requests
import bs4 as bs
from django.db import IntegrityError
from ...models import Currency


def save_currency():
    link = 'https://transferwise.com/gb/blog/world-currency-symbols'
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    tables = soup.findAll('table', {'class': 'table table-bordered'})[:4]

    for table in tables:
        for row in table.findAll('tr')[1:]:
            name = row.findAll('td')[1].text
            code = row.findAll('td')[2].text
            symbol = row.findAll('td')[3].text
            unicode_char = row.findAll('td')[4].text
            html_symbol = row.findAll('td')[5].text
            hex_code = row.findAll('td')[6].text

            print(symbol)

            try:
                Currency.objects.create(code=code, name=name, symbol=symbol, unicode_char=unicode_char,
                                        html_symbol=html_symbol, hex_code=hex_code)
                print('Added {} to currency table'.format(name))

            except IntegrityError:
                print('{} is already a recorded currency'.format(name))
