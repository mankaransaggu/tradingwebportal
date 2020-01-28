import pandas as pd
from django.db import IntegrityError

from ...models import Currency


def format_df(df):
    df = df.rename(
        columns={'currency code': 'code', 'currency name': 'name'})

    return df


def df_to_sql(df):
    for row in df.itertuples():

        try:
            print(row)
            Currency.objects.create(code=getattr(row, 'code'), name=getattr(row, 'name'))

        except IntegrityError:
            print('Currency {} already exists'.format(getattr(row, 'code')))
