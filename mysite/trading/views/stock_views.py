from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic

from ..backend.stock.stock_detail_data import create_detail_data
from ..backend.account import account_bookmarks, account_positions
from ..models import Stock


class StocksView(generic.ListView):
    model = Stock
    template_name = 'stock/stock_listing.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        return Stock.objects.all().order_by('ticker')

    def get_context_data(self, **kwargs):
        context = super(StocksView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.check_stock_list(user, context)
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context


class StockDetailView(generic.DetailView):
    model = Stock
    template_name = 'stock/stock_detail.html'

    def get_context_data(self, **kwargs):
        context = super(StockDetailView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user
        pk = self.kwargs['pk']

        stock = get_object_or_404(Stock, pk=pk)
        # Creates the stock charts and the change summary
        create_detail_data(stock, context)

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.check_is_favourite(user, stock, context)
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context


def favourite_stock(request, id):
    user = request.user

    if not user.is_verified:
        messages.info(request, 'Please verify your account before bookmarking instruments')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        stock = get_object_or_404(Stock, id=id)

        if stock.favourite.filter(id=request.user.id).exists():
            stock.favourite.remove(request.user)
        else:
            stock.favourite.add(request.user)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))