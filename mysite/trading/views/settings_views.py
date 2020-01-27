from itertools import count

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange
from django.contrib import messages
from django.views.generic import TemplateView

from ..backend.account import account_bookmarks, account_positions
from ..backend.exchange.exchange import NYSE, NASDAQ
from ..models import Stock
from ..backend.stock.stock_data import update_market_data
from ..backend.fx.fx_data import save_pairs_and_data
from ..backend.fx.currency import save_currency
from ..backend.fx.fx_data import get_fx_data, test


class SearchView(TemplateView):
    template_name = 'search.html'

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '')
        self.results = Stock.objects.filter(name__icontains=q, ticker__icontains=q)
        return super().get(request=self.results, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(results=self.results, **kwargs)


class Setting(TemplateView):
    template_name = 'trading/settings.html'
    setting = None

    def get_context_data(self, **kwargs):
        context = super(Setting, self).get_context_data(**kwargs)
        setting = self.request.GET.get('setting')
        request = self.request
        user = request.user

        if user.is_authenticated:
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

            if setting == 'download-nyse':
                NYSE().save_stocks()
                messages.success(request, "%s SQL statements were executed." % count)

            if setting == 'download-nasdaq':
                NASDAQ().save_stocks()
                messages.success(request, "%s SQL statements were executed." % count)

            if setting == 'download-stocks':
                NYSE().save_stocks()
                print('NYSE complete')
                NASDAQ().save_stocks()
                print('NASDAQ complete')

            if setting == 'update-stocks':
                update_market_data()

            if setting == 'fx-pairs':
                save_pairs_and_data()

            if setting == 'get-currency':
                save_currency()

            if setting == 'get-fx':
                get_fx_data()

            if setting == 'te':
                test()

            # if setting == 'yahoo':
            #     ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
            #     data, meta_data = ts.get_intraday(symbol='AAPL')
            #     print(data)
            #
            # if setting == 'fx':
            #     fx = ForeignExchange(key='3GVY8HKU0D7L550R', output_format='pandas')
            #     data, meta_data = fx.get_currency_exchange_daily('USD', 'GBP')
            #     print(data)


        return context