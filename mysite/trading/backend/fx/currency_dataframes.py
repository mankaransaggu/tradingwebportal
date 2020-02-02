import pandas as pd
from django.db import IntegrityError

from ...models import Currency


def format_df(df):
    df = df.rename(
        columns={'currency code': 'code', 'currency name': 'name'})

    return df


def df_to_sql(df):
    active_currencys = ['USD', 'GBP', 'CNY', 'CAD', 'EUR', ]
    for row in df.itertuples():
        print(row)

        if getattr(row, 'code') in active_currencys:
            Currency.objects.update_or_create(code=getattr(row, 'code'), name=getattr(row, 'name'), active=True)
        else:
            Currency.objects.update_or_create(code=getattr(row, 'code'), name=getattr(row, 'name'))
