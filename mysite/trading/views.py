from django.shortcuts import render
from django.views.generic import TemplateView
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
from .backend import get_nyse_data
from .backend import database as db

pd.core.common.is_list_like = pd.api.types.is_list_like


def home(request):
    return render(request, 'trading/chart.html')


def settings(request):
    return render(request, 'trading/settings.html')


class Graph(TemplateView):
    template_name = 'trading/chart.html'
    ticker = None

    def get_context_data(self, **kwargs):
        context = super(Graph, self).get_context_data(**kwargs)
        context['ticker'] = self.request.GET.get('ticker')
        ticker = self.request.GET.get('ticker')
        print(ticker)
        #df = db.create_stock_df(ticker)

        # Calls method to create market data dataframe from sql query
        df = db.create_df(ticker)

        # Create the two
        df_ohlc = df['adj_close'].resample('10D').ohlc()
        df_volume = df['volume'].resample('10D').sum()

        df_ohlc.reset_index(inplace=True)
        df_ohlc['date'] = df_ohlc['date'].map(mdates.date2num)

        fig = go.Figure(data=[go.Candlestick(x=df.index,
                                             open=df['open'],
                                             high=df['high'],
                                             low=df['low'],
                                             close=df['close']
                                             )])
        div = opy.plot(fig, auto_open=False, output_type='div')

        context['graph'] = div

        return context


class Settings(TemplateView):
    template_name = 'trading/settings.html'

    def get_context_data(self, **kwargs):
        context = super(Settings, self).get_context_data(**kwargs)

        context['start'] = 'Getting data'
        get_nyse_data.save_nyse_tickers()

        context['finish'] = 'finished'

        return context
