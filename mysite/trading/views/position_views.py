import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import FormView

from ..backend.fx.fx_data import get_exchange_rate
from ..backend.account import account_bookmarks, account_positions
from ..forms import CreatePositionForm
from ..models import Stock, User, Position
from ..backend.stock.stock_dates import get_latest
from django.utils import timezone


class OpenPositionForm(FormView):
    template_name = 'trading/open_position.html'
    form_class = CreatePositionForm
    success_url = ('account/')
    model = Position

    def get_initial(self):
        initial = super(OpenPositionForm, self).get_initial()

        request = self.request
        id = self.kwargs['id']
        instrument = Stock.objects.get(id=id)
        latest = get_latest(instrument)

        if latest is None:
            messages.warning(request, 'This instrument has no recorded data')

        initial['stock'] = instrument
        initial['open_date'] = datetime.datetime.now()
        initial['open_price'] = latest.close

        return initial

    def form_valid(self, form):
        request = self.request
        user = request.user
        user = User.objects.get(id=user.id)

        if not user.is_verified:
            messages.info(request, 'Please verify your account before opening positions')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        elif form.is_valid:
            user = self.request.user

            post = form.save(commit=False)
            post.user = user
            post.value = post.open_price * post.quantity

            stock = post.stock
            stock_currency = stock.exchange.get_currency()

            if stock_currency is not user.base_currency:
                rate = get_exchange_rate(stock_currency, user.base_currency)
                post.value = post.value * rate.close
                print('rate {}'.format(rate.close))
                print('value {}'.format(post.value))

            if user.funds < post.value:
                messages.warning(request, 'You do not have the required funds to open this position')
            else:
                post.position_state = 'Open'
                post.save()

                user.funds = user.funds - post.value
                user.save()
                user.get_account_value()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    def get_context_data(self, **kwargs):
        context = super(OpenPositionForm, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            account_bookmarks.get_user_favourites(user, context)
            account_positions.get_open_positions(user, context)

        return context


def close_position(request, id):
    position = Position.objects.get(id=id)
    user = request.user
    account = User.objects.get(id=user.id)

    stock = Stock.objects.get(ticker=position.instrument)
    close = get_latest(stock)
    close_price = close.close

    position.close_price = close_price
    position.close_date = timezone.now()
    position.open = False

    if position.direction == 'BUY':
        result = (close_price - position.open_price) * position.quantity
    else:
        result = (position.open_price - close_price) * position.quantity

    position.result = result
    if result > 0:
        account.value = account.value + result
        account.result = account.result  + result
    else:
        account.value = account.value - result
        account.result = account.result - result

    position.save()
    account.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))








