from django.shortcuts import get_object_or_404
from django.views import generic

from ..backend.account import account_bookmarks, account_positions
from ..models import Stock, Exchange


class ExchangeListView(generic.ListView):
    template_name = 'exchange/exchange_list.html'
    context_object_name = 'exchanges'

    def get_queryset(self):
        return Exchange.objects.all().order_by('country')

    def get_context_data(self, **kwargs):
        context = super(ExchangeListView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context


class ExchangeDetailView(generic.DetailView):
    model = Exchange
    template_name = 'exchange/exchange_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ExchangeDetailView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user
        pk = self.kwargs['pk']

        exchange = get_object_or_404(Exchange, pk=pk)
        account_bookmarks.get_user_favourites(user, context)
        account_positions.get_open_positions(user, context)

        return context


class ExchangeStocksListView(generic.ListView):
    template_name = 'exchange/exchange_stocks.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        pk = self.kwargs['pk']
        return Stock.objects.filter(exchange_id=pk).order_by('ticker')

    def get_context_data(self, **kwargs):
        context = super(ExchangeStocksListView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        pk = self.kwargs['pk']
        exchange = Exchange.objects.get(id=pk)
        context['exchange'] = exchange

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.check_exchange_stock(user, exchange, context)
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context
