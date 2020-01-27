from django.shortcuts import get_object_or_404
from django.views import generic

from ..backend.account import account_bookmarks, account_positions
from ..models import Currency, FX


class CurrencyListView(generic.ListView):
    template_name = 'currency/currency_list.html'
    context_object_name = 'currencies'

    def get_queryset(self):
        return Currency.objects.all().order_by('-active')

    def get_context_data(self, **kwargs):
        context = super(CurrencyListView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context


class CurrencyDetailView(generic.DetailView):
    template_name = 'currency/currency_detail.html'
    model = Currency

    def get_context_data(self, **kwargs):
        context = super(CurrencyDetailView, self).get_context_data(**kwargs)
        request = self.request
        pk = self.kwargs['pk']

        currency = get_object_or_404(Currency, id=pk)
        currency_pairs = currency.get_pairs()

        context['pairs'] = currency_pairs

        return context


class FXDetailView(generic.DetailView):
    template_name = 'currency/fx_pair.html'
    model = FX

    def get_context_data(self, **kwargs):
        context = super(FXDetailView, self).get_context_data(**kwargs)
        request = self.request
        pk = self.kwargs['pk']

        fx = get_object_or_404(FX, pk=pk)

        return context