from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.views.generic import TemplateView
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
from .backend import get_nyse_data
from .backend import database as db

from django.contrib.sites.shortcuts import get_current_site

from django.template.loader import render_to_string
from .forms import SignUpForm
from .tokens import account_activation_token

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode
from django.contrib import messages

from .models import Favourites, Exchange, Stock, MarketData

pd.core.common.is_list_like = pd.api.types.is_list_like


def home(request):
    return render(request, 'trading/chart.html', {'favourites': sidebar(request)})


class Setting(TemplateView):
    template_name = 'trading/settings.html'
    setting = None

    def get_context_data(self, **kwargs):
        context = super(Setting, self).get_context_data(**kwargs)
        context['setting'] = self.request.GET.get('setting')
        request = self.request
        context['favourites'] = sidebar(request)

        setting = context['setting']
        print(setting)

        if setting == 'download':
            get_nyse_data.save_nyse_tickers()
            print(context['setting'])

        return context


class Search(TemplateView):
    template_name = 'trading/exchange_stocks.html'

    def get_context_data(self, **kwargs):
        context = super(Search, self).get_context_data(**kwargs)

        context = get_exchange_stocks(self, context)

        if context['found'] is False:
            context = super(Search, self).get_context_data(**kwargs)
            context = get_stock_graph(self, context)
            self.template_name = 'trading/chart.html'

            if context['found'] is True:
                return context

        return context


def get_stock_graph(self, context):
    context['ticker'] = self.request.GET.get('search')
    symbol = context['ticker']
    request = self.request
    context['favourites'] = sidebar(request)

    # Calls method to create market data dataframe from sql query
    try:
        df = db.create_df(symbol)

        # Create the two
        df_ohlc = df['adj_close'].resample('10D').ohlc()
        df_volume = df['volume'].resample('10D').sum()

        df_ohlc.reset_index(inplace=True)
        df_ohlc['date'] = df_ohlc['date'].map(mdates.date2num)

        fig = go.Figure(data=[go.Candlestick(x=df.index,
                                             open=df['open'],
                                             high=df['high'],
                                             low=df['low'],
                                             close=df['close']
                                             )])
        div = opy.plot(fig, auto_open=False, output_type='div')

        context['graph'] = div
        context['found'] = True

    except:
        context['found'] = False
        context['message'] = symbol + ' Is Not A Listed Exchange Or Stock'
        return context

    return context


def get_exchange_stocks(self, context):
    symbol = self.request.GET.get('search')

    try:
        exchange = Exchange.objects.get(code=symbol)
        context['exchange'] = exchange.code
        stock_list = Stock.objects.filter(exchange__code=exchange.code).order_by('ticker')

        context['found'] = True

        paginator = Paginator(stock_list, 50)
        page = self.request.GET.get('page')

        try:
            stocks = paginator.page(page)
        except PageNotAnInteger:
            stocks = paginator.page(1)
        except EmptyPage:
            stocks = paginator.page(paginator.num_pages)

        context['stocks'] = stocks

        return context

    except:
        context['found'] = False
        context['message'] = symbol + ' Is Not A Listed Exchange Or Stock'
        return context

    return context


def stock_list(request):
    stock_list = Stock.objects.all().order_by('ticker')
    paginator = Paginator(stock_list, 100)
    page = request.GET.get('page')

    try:
        stocks = paginator.page(page)
    except PageNotAnInteger:
        stocks = paginator.page(1)
    except EmptyPage:
        stocks = paginator.page(paginator.num_pages)

    return render(request,
                  'trading/stocks.html',
                  {'stocks': stocks})


def exchange_list(request):
    exchange_list = Exchange.objects.all()
    paginator = Paginator(exchange_list, 100)
    page = request.GET.get('page')

    try:
        exchanges = paginator.page(page)
    except PageNotAnInteger:
        exchanges = paginator.page(1)
    except EmptyPage:
        exchanges = paginator.page(paginator.num_pages)

    return render(request,
                  'trading/exchanges.html',
                  {'exchanges': exchanges})


def exchange_stocks(request):
    exchange = request.GET.get('exchange')
    try:

        stock_list = Stock.objects.filter(exchange__code=exchange).order_by('ticker')

        paginator = Paginator(stock_list, 50)
        page = request.GET.get('page')

        try:
            stocks = paginator.page(page)
        except PageNotAnInteger:
            stocks = paginator.page(1)
        except EmptyPage:
            stocks = paginator.page(paginator.num_pages)

        return render(request,
                      'trading/exchange_stocks.html',
                      {'stocks': stocks})

    except:
        message = exchange + ' Is Not A Listed Exchange Or Stock'

        return render(request,
                      'trading/exchange_stocks.html',
                      {'message': message})

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


def sidebar(request):
    if request.user.is_authenticated:
        favourites = Favourites.objects.filter(account=request.user)
        return favourites

    else:
        return 'None'


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
    return render(request,
                  'trading/account.html',
                  {'favourites': sidebar(request)})
