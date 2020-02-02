import MySQLdb
import sqlalchemy
from django.db import IntegrityError

import pandas as pd

from ...models import FX, FXPriceData, DataType


def format_df(df, fx):
    df = df.rename(
        columns={'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close'})
    df.rename_axis('timestamp', axis='index', inplace=True)
    df['fx'] = fx
    df.index = pd.to_datetime(df.index)
    data = DataType.objects.get(code='DAILY')
    df['data_type'] = data
    print(df)
    return df


def df_to_sql(df):
    # Flip the data in the df, so it goes from latest to earliest data
    df = df.iloc[:-1]

    for row in df.itertuples():

        try:
            print(row)
            FXPriceData.objects.create(timestamp=getattr(row, 'Index'), high=getattr(row, 'high'),
                                       low=getattr(row, 'low'), open=getattr(row, 'open'),
                                       close=getattr(row, 'close'), currency_pair=getattr(row, 'fx'),
                                       data_type=getattr(row, 'data_type'))

        except (IntegrityError, sqlalchemy.exc.IntegrityError, MySQLdb._exceptions.IntegrityError) as e:
            print('Error {} on row {}'.format(e, getattr(row, 'fx')))
            break
