import MySQLdb
import sqlalchemy
from django.db import IntegrityError
from ..models import IntradayData


def df_to_sql(df):
    for index, row in df.iterrows():

        try:
            timestamp = index
            high = row['high']
            low = row['low']
            open = row['open']
            close = row['close']
            volume = row['volume']
            instrument = row['instrument_id']

            IntradayData.objects.update_or_create(timestamp=timestamp, high=high, low=low, open=open,
                                                  close=close, volume=volume, instrument_id=instrument)

        except IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break

        except MySQLdb._exceptions.IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break

        except sqlalchemy.exc.IntegrityError:
            print('Data {} already exists'.format(row['instrument_id']))
            break
