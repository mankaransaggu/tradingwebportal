from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import generic

from django.views.generic import TemplateView
from django.template.loader import render_to_string

import pandas as pd

from .backend import get_nyse_data
from .backend import stock_data as data
from .forms import SignUpForm
from .tokens import account_activation_token
from .models import Favourites, Exchange, Stock, MarketData
from .backend import database as db

import threading
pd.core.common.is_list_like = pd.api.types.is_list_like


class IndexView(generic.ListView):
    template_name = 'trading/index.html'
    context_object_name = 'latest_stock_list'

    def get_queryset(self):
        return MarketData.objects.order_by('-date')[:5]


class ExchangesView(generic.ListView):
    template_name = 'trading/exchanges.html'
    context_object_name = 'exchanges'

    def get_queryset(self):
        return Exchange.objects.all()


class ExchangeStocksView(generic.ListView):
    template_name = 'trading/exchange_stocks.html'
    context_object_name = 'stocks'

    def get_queryset(self):
        return Stock.objects.order_by('ticker')


class StocksView(generic.ListView):
    template_name = 'trading/stocks.html'
    context_object_name = 'stocks'

    def get_queryset(self):
        return Stock.objects.order_by('-ticker')


class StockView(generic.DetailView):
    model = Stock
    template_name = 'trading/detail.html'

    def get_context_data(self, **kwargs):
        context = super(StockView, self).get_context_data(**kwargs)
        pk = self.kwargs['pk']
        stock = Stock.objects.get(id=pk)

        context['graph'] = data.create_stock_chart(100, stock)
        # Get yesterdays and YTD data
        data.get_view_context(context, stock.ticker)

        return context


class Setting(TemplateView):
    template_name = 'trading/settings.html'
    setting = None

    def get_context_data(self, **kwargs):
        context = super(Setting, self).get_context_data(**kwargs)
        context['setting'] = self.request.GET.get('setting')
        request = self.request
        context['favourites'] = sidebar(request)

        setting = context['setting']

        if setting == 'download':
            get_nyse_data.save_nyse_tickers()
            context['messages'] = 'Data saving'

        return context


def signup(request):
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
        return redirect('home')
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
    logout(request)
    messages.info(request, 'Logged Out')

    return redirect('home')


def account(request):
    positions = ''
    return render(request,
                  'trading/account.html',
                  {'favourites': sidebar(request),
                   'positions': positions})


def sidebar(request):
    if request.user.is_authenticated:
        favourites = Favourites.objects.filter(account=request.user)
        return favourites

    else:
        return 'None'
