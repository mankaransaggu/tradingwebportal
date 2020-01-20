import datetime

from django.http import HttpResponseRedirect
from django.views.generic import FormView

from mysite.trading.backend import stock_data, user_positions, user_bookmarks
from mysite.trading.forms import CreatePositionForm
from mysite.trading.models import Stock, Account, Position


class OpenPositionForm(FormView):
    template_name = 'trading/open_position.html'
    form_class = CreatePositionForm
    success_url = ('account/')
    model = Position

    def get_initial(self):
        initial = super(OpenPositionForm, self).get_initial()

        id = self.kwargs['id']
        instrument = Stock.objects.get(id=id)
        latest = stock_data.get_latest(instrument)

        initial['instrument'] = instrument
        initial['open_date'] = datetime.now()
        initial['open_price'] = latest.close

        return initial

    def form_valid(self, form):
        request = self.request
        user = request.user
        account = Account.objects.get(id=user.id)

        post = form.save(commit=False)
        post.account_id = self.request.user.pk
        post.position_state = 'Open'
        post.save()

        account.value = post.open_price * post.quantity
        account.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    def get_context_data(self, **kwargs):
        context = super(OpenPositionForm, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        if user.is_authenticated:
            # Methods that deal with user favourites and positions
            user_bookmarks.get_user_favourites(user, context)
            user_positions.get_open_positions(user, context)

        return context


def close_position(request, id):
    position = Position.objects.get(id=id)
    user = request.user
    account = Account.objects.get(id=user.id)

    stock = Stock.objects.get(ticker=position.instrument)
    close = stock_data.get_latest(stock)
    close_price = close.close

    position.close_price = close_price
    position.close_date = datetime.now()
    position.open = False

    if position.direction == 'BUY':
        result = (close_price - position.open_price) * position.quantity
    else:
        result = (position.open_price - close_price) * position.quantity

    position.result = result
    if result > 0:
        account.value = account.value + result
        account.earned = account.earned + result
    else:
        account.value = account.value - result
        account.earned = account.earned - result

    position.save()
    account.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))








