from .currency_dataframes import format_df, df_to_sql
import pandas as pd


def save_currencies():
    df = pd.read_csv('https://www.alphavantage.co/physical_currency_list/')
    df = format_df(df)
    df_to_sql(df)

