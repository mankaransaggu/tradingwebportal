from datetime import datetime
from itertools import count

from bootstrap_modal_forms.mixins import PassRequestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponseRedirect, request
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode

from django.views import generic

from django.views.generic import TemplateView, FormView
from django.template.loader import render_to_string

import pandas as pd

from .backend import get_nyse_data, get_nasdaq_data
from .backend import stock_data as data
from .forms import SignUpForm, EditAccountForm, CreatePositionForm
from .tokens import account_activation_token
from .models import Exchange, Stock, MarketData, Position, Account
from .backend import database as db
from .backend.exchange import NYSE, NASDAQ

import threading

pd.core.common.is_list_like = pd.api.types.is_list_like


class IndexView(generic.ListView):
    template_name = 'trading/index.html'
    context_object_name = 'latest_stock_list'

    def get_queryset(self):
        return MarketData.objects.order_by('-date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['favourites'] = sidebar(self.request)
        context['open_positions'] = footer(self.request)
        return context


class ExchangesView(generic.ListView):
    template_name = 'trading/exchanges.html'
    context_object_name = 'exchanges'

    def get_queryset(self):
        return Exchange.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ExchangesView, self).get_context_data(**kwargs)
        context['favourites'] = sidebar(self.request)
        context['open_positions'] = footer(self.request)
        return context


class ExchangeStocksView(generic.ListView):
    template_name = 'trading/exchange_stocks.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        pk = self.kwargs['pk']

        return Stock.objects.filter(exchange_id=pk).order_by('ticker')

    def get_context_data(self, **kwargs):
        context = super(ExchangeStocksView, self).get_context_data(**kwargs)
        context['favourites'] = sidebar(self.request)
        context['open_positions'] = footer(self.request)
        return context


class StocksView(generic.ListView):
    model = Stock
    template_name = 'trading/stocks.html'
    context_object_name = 'stocks'
    paginate_by = 50

    def get_queryset(self):
        return Stock.objects.all().order_by('ticker')

    def get_context_data(self, **kwargs):
        context = super(StocksView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        favourites = Stock.objects.filter(favourite__pk=user.pk).only('id', 'ticker')
        count = Exchange.objects.annotate(num_stocks=Count('stock'))

        context['stock_count'] = count
        context['favourites'] = favourites
        context['open_positions'] = footer(self.request)
        return context


class StockView(generic.DetailView):
    model = Stock
    template_name = 'trading/detail.html'

    def get_context_data(self, **kwargs):
        context = super(StockView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        pk = self.kwargs['pk']
        stock = get_object_or_404(Stock, pk=pk)

        is_favourite = False
        if stock.favourite.filter(id=user.id).exists():
            is_favourite = True

        open_positions = Position.objects.filter(account_id=user.pk, instrument__id=pk, open=True)
        close_positions = Position.objects.filter(account_id=user.pk, instrument__id=pk,
                                                  open=False)

        context['graph'] = data.create_stock_chart(365, stock, open_positions)
        context['summary'] = data.create_stock_change(stock)
        context['open_positions'] = open_positions
        context['close_positions'] = close_positions
        context['favourites'] = sidebar(request)
        context['is_favourite'] = is_favourite
        context['open_positions'] = footer(self.request)
        data.get_view_context(context, stock.ticker)

        return context


class OpenPositionForm(FormView):
    template_name = 'trading/open_position.html'
    form_class = CreatePositionForm
    success_url = ('account/')
    model = Position

    def get_initial(self):
        initial = super(OpenPositionForm, self).get_initial()

        id = self.kwargs['id']
        instrument = Stock.objects.get(id=id)
        latest = data.get_yesterday(instrument.ticker)

        initial['instrument'] = instrument
        initial['open_date'] = datetime.now()
        initial['open_price'] = latest.close_price
        return initial

    def form_valid(self, form):
        post = form.save(commit=False)
        post.account_id = self.request.user.pk
        post.position_state = 'Open'
        post.save()
        return redirect('account')

    def get_context_data(self, **kwargs):
        context = super(OpenPositionForm, self).get_context_data(**kwargs)
        context['favourites'] = sidebar(self.request)
        context['open_positions'] = footer(self.request)
        return context


def close_position(request, id):
    position = Position.objects.get(id=id)
    user = request.user
    account = Account.objects.get(id=user.id)

    stock = Stock.objects.get(ticker=position.instrument)
    close = data.get_yesterday(stock.ticker)
    close_price = close.close_price

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


class AccountView(TemplateView):
    model = User
    template_name = 'account/account.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super(AccountView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        request = self.request
        user = request.user

        if request.user.is_authenticated:
            favourites = user.favourite.all().order_by('ticker')
            positions = Position.objects.filter(account_id=request.user.pk).order_by('-open')
            context['positions'] = positions

            for fav in favourites.iterator():
                is_favourite = False
                stock = get_object_or_404(Stock, id=fav.id)
                if stock.favourite.filter(id=user.id).exists():
                    is_favourite = True

                context['is_favourite'] = is_favourite
            context['favourites'] = favourites
            context['open_positions'] = footer(self.request)
            return context

        else:
            messages.success(request, "Please log in")
            return context


class Setting(TemplateView):
    template_name = 'trading/settings.html'
    setting = None

    def get_context_data(self, **kwargs):
        context = super(Setting, self).get_context_data(**kwargs)
        context['setting'] = self.request.GET.get('setting')
        request = self.request
        context['favourites'] = sidebar(request)
        context['open_positions'] = footer(self.request)

        setting = context['setting']

        if request.user.is_authenticated:

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

            return context
        else:
            return context


def sidebar(request):
    if request.user.is_authenticated:
        user = request.user
        favourites = user.favourite.all()
        return favourites
    else:
        return 'None'


def footer(request):
    if request.user.is_authenticated:
        user = request.user
        open_positions = Position.objects.filter(account=user, open=True).order_by('open_date')
        return open_positions


def favourite_stock(request, id):
    stock = get_object_or_404(Stock, id=id)

    if stock.favourite.filter(id=request.user.id).exists():
        stock.favourite.remove(request.user)
    else:
        stock.favourite.add(request.user)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def signup(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = SignUpForm(request.POST)

            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                current_site = get_current_site(request)
                subject = 'Activate Your Trading Account'
                message = render_to_string('trading/account_activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                user.email_user(subject, message)
                return redirect('account_activation_sent')

            else:
                for msg in form.error_messages:
                    messages.error(request, f"{msg}: {form.error_messages[msg]}")

                    return render(request,
                                  "trading/signup.html",
                                  {"form": form})

        else:
            form = SignUpForm()
        return render(request, 'trading/signup.html', {'form': form})

    else:
        return redirect('index')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.account.email_confirmed = True
        user.save()
        login(request, user)
        messages.success(request, f"New account activated: {user.email}")
        return redirect('index')
    else:
        return render(request, 'trading/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'trading/account_activation_sent.html')


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request,
                  'trading/login.html',
                  {'form': form})


def logout_request(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Logged Out')

        return redirect('index')
    else:
        return redirect('index')


def edit_account(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            form = EditAccountForm(request.POST, instance=request.user)

            if form.is_valid():
                form.save()
                return redirect('/account')

        else:
            form = EditAccountForm(instance=request.user)
            args = {'form': form}
            return render(request,
                          'account/edit_account.html',
                          args)
    else:
        return redirect('login')


def change_password(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            form = PasswordChangeForm(data=request.POST, user=request.user)

            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                return redirect('/account')
            else:
                return redirect('/account/change_password')

        else:
            form = PasswordChangeForm(user=request.user)
            args = {'form': form}
            return render(request,
                          'account/change_password.html',
                          args)
    else:
        return redirect('login')



