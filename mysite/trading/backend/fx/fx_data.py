from django.shortcuts import get_object_or_404
from alpha_vantage.foreignexchange import ForeignExchange
from ...models import Currency, FX, FXPriceData, Instrument
from .fx_dataframes import format_df, df_to_sql


def save_currency_pairs():
    currencies = Currency.objects.all()
    instrument = get_object_or_404(Instrument, code='FX')

    for from_currency in currencies:
        for to_currency in currencies:
            if from_currency != to_currency:
                code = from_currency.code + '/' + to_currency.code
                FX.objects.update_or_create(code=code, from_currency=from_currency, to_currency=to_currency,
                                            instrument=instrument)


def get_fx_data():
    fx_pairs = FX.objects.all()
    for fx in fx_pairs:
        exchange = ForeignExchange(key='3GVY8HKU0D7L550R', output_format='pandas')
        data, meta_data = exchange.get_currency_exchange_daily(fx.from_currency.code, fx.to_currency.code)

        df = format_df(data, fx)
        df_to_sql(df)


def save_pairs_and_data():
    save_currency_pairs()
    get_fx_data()
