from .account_views import *
from .settings_views import *
from .position_views import *
from .exchange_views import *
from .stock_views import *
from .currency_views import *

from django.views import generic
from django.contrib.auth.forms import AuthenticationForm

from ..backend.account import account_bookmarks, account_positions
from ..models import StockPriceData


class IndexView(generic.ListView):
    template_name = 'trading/index.html'
    context_object_name = 'latest_stock_list'

    def get_queryset(self):
        return None

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        # Check the user is logged in before searching
        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)
        else:
            context['form'] = AuthenticationForm(request=request, data=request.POST)

        return context
