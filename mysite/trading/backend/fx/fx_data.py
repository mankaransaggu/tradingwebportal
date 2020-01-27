from django.shortcuts import get_object_or_404
from alpha_vantage.foreignexchange import ForeignExchange
from ...models import Currency, FX, FXPriceData, Instrument
from .fx_dataframes import format_df, df_to_sql
import time
import datetime


def save_currency_pairs():
    currencies = Currency.objects.filter(active=True)
    instrument = get_object_or_404(Instrument, code='FX')

    for from_currency in currencies:
        for to_currency in currencies:
            if from_currency != to_currency:
                code = from_currency.code + '/' + to_currency.code
                FX.objects.update_or_create(code=code, from_currency=from_currency, to_currency=to_currency,
                                            instrument=instrument)


def get_fx_data():
    fx_pairs = FX.objects.all()
    count = 0;

    for fx in fx_pairs:

        latest = FXPriceData.objects.filter(currency_pair=fx).order_by('-timestamp').first()
        if latest and latest.timestamp == datetime.datetime.today():
            print('Latest data for {} already stored'.format(fx))
        else:
            try:
                # Check if I have hit alphas api limit, if so wait 1 min
                count += 1
                if count == 6:
                    time.sleep(70)
                    count = 0

                exchange = ForeignExchange(key='3GVY8HKU0D7L550R', output_format='pandas')
                data, meta_data = exchange.get_currency_exchange_daily(from_symbol=fx.from_currency.code,
                                                                       to_symbol=fx.to_currency.code, outputsize='full')

                # Format the dataframe and save the data in the db
                df = format_df(data, fx)
                df_to_sql(df)
            except ValueError as e:
                print('{} - Pair: {}'.format(e, fx))


def save_pairs_and_data():
    save_currency_pairs()
    get_fx_data()
