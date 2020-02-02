from django.core.management import BaseCommand
from django.db.backends.utils import logger
from ...models import Instrument, DataType, Currency, Country, Exchange, Stock, StockPriceData, FX, FXPriceData, \
    Position
from ...backend.fx.currency import save_currencies
from ...backend.fx.fx_data import save_pairs_and_data, save_currency_pairs, get_fx_data
from ...backend.exchange.exchange import NASDAQ, NYSE

# python manage.py seed --mode=refresh

"""Clear all data and creates Currencies"""
MODE_REFRESH = 'refresh'

"""Clear all data and doesnt create any data"""
MODE_CLEAR = 'clear'


class Command(BaseCommand):
    help = 'Seed the database for development'

    def add_arguments(self, parser):
        parser.add_argument('--mode', type=str, help='Mode')

    def handle(self, *args, **options):
        self.stdout.write('seeding data...')
        run_seed(self, options['mode'])
        self.stdout.write('done')


def clear_data():
    """Deletes all table data"""
    logger.info('Delete all Object instances')

    Position.objects.all().delete()
    FXPriceData.objects.all().delete()
    FX.objects.all().delete()
    StockPriceData.objects.all().delete()
    Stock.objects.all().delete()
    Exchange.objects.all().delete()
    Country.objects.all().delete()
    Currency.objects.all().delete()
    DataType.objects.all().delete()
    Instrument.objects.all().delete()


def create_instrument():
    """Creates the needed Instrument objects"""
    logger.info('Creating Instruments...')
    instrument_codes = ['STOCK', 'FX', 'BOND', 'INDICIE']
    instrument_names = ['Stocks', 'Foreign Exchange', 'Bonds', 'Indicies']
    instrument_descriptions = ['Company shares', 'Foreign exchange instruments', 'Treasuries/Corporate bonds',
                               'Stock indicies']

    for code, name, description in zip(instrument_codes, instrument_names, instrument_descriptions):
        Instrument.objects.update_or_create(code=code, name=name,
                                            description=description)

        logger.info('{} instrument created'.format(Instrument.code))


def create_currency():
    """Create the Currency and FX objects"""
    logger.info('Creating Currencies..')
    save_currencies()
    logger.info('Created Currencies')
    logger.info('Creating Currency Pairs..')
    save_currency_pairs()
    logger.info('Created Currency Pairs')
    logger.info('Creating FX Data...')
    get_fx_data()
    logger.info('Created FX Data')


def create_country():
    """Creates the Country objects"""
    logger.info('Creating Countries..')

    country_codes = ['USA', 'UK', 'CN', 'CAN', 'GER']
    country_names = ['United States of America', 'United Kingdom', 'China', 'Canada', 'Germany']
    country_currencies = ['USD', 'GBP', 'CNY', 'CAD', 'EUR']

    for code, name, currency_code in zip(country_codes, country_names, country_currencies):
        cur = Currency.objects.get(code=currency_code)
        Country.objects.update_or_create(code=code, name=name, currency=cur)

        logger.info('{} Country created'.format(Country.code))


def create_exchange():
    """Creates the Exchange objects"""
    logger.info('Creating Exchanges..')

    exchange_codes = ['NYSE', 'NASDAQ', 'LSE', 'SSE']
    exchange_names = ['New York Stock Exchange', 'NASDAQ Stock Market', 'London Stock Exchange',
                      'Shanghai Stock Exchange']
    exchange_countries = ['USA', 'USA', 'UK', 'CN']

    for code, name, country in zip(exchange_codes, exchange_names, exchange_countries):
        location = Country.objects.get(code=country)
        Exchange.objects.update_or_create(code=code, name=name, country=location)

        logger.info('{} Exchange created'.format(Exchange.code))


def create_data_type():
    """Creates the DataType objects"""
    logger.info('Creating Data Types..')

    data_codes = ['DAILY', 'INTRADAY']
    data_description = ['Data for a 24 period', 'Data for a 1 minute perioo']

    for code, description in zip(data_codes, data_description):
        DataType.objects.update_or_create(code=code, description=description)

        logger.info('{} DataType created'.format(DataType.code))


def create_stocks():
    """Creates the Stock objects"""
    logger.info('Creating Stocks and Stock Data...')
    logger.info('Adding NYSE Stocks...')
    NYSE().save_stocks()
    logger.info('Added NYSE Stocks')
    logger.info('Adding NASDAQ Stocks...')
    NASDAQ().save_stocks()
    logger.info('Added NASDAQ Stocks')


def run_seed(self, mode):
    """ Seed the database based on mode

    :param self:
    :param mode: refresh / clear
    :return:
    """

    if mode == MODE_CLEAR:
        clear_data()
        return

    create_data_type()
    create_instrument()
    create_currency()
    create_country()
    create_exchange()
    create_stocks()
