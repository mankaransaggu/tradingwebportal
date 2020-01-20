from itertools import count

from alpha_vantage.timeseries import TimeSeries
from django.contrib import messages
from django.views.generic import TemplateView

from mysite.trading.backend import user_bookmarks, user_positions
from mysite.trading.backend.exchange import NYSE, NASDAQ
from mysite.trading.models import Stock


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

        if request.user.is_authenticated:

            user_bookmarks.get_user_favourites(user, context)
            user_positions.get_open_positions(user, context)

            if setting == 'download-nyse':
                NYSE().save_stocks()
                messages.success(request, "%s SQL statements were executed." % count)

            if setting == 'download-nasdaq':
                NASDAQ().save_stocks()
                messages.success(request, "%s SQL statements were executed." % count)

            if setting == 'update-nasdaq':
                NASDAQ().update_market_data()
                messages.success(request, "%s SQL statements were executed." % count)

            if setting == 'update-nyse':
                NYSE().update_market_data()
                messages.success(request, "Update success with new class")

            if setting == 'yahoo':
                ts = TimeSeries(key='3GVY8HKU0D7L550R', output_format='pandas')
                data, meta_data = ts.get_monthly(symbol='AAPL')
                print(data)

            return context
        else:
            return context