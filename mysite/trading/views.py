from django.shortcuts import render
from django.views.generic import TemplateView
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
from .backend import get_nyse_data
from .backend import database as db

from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .forms import SignUpForm
from .tokens import account_activation_token

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode

pd.core.common.is_list_like = pd.api.types.is_list_like


def home(request):
    return render(request, 'trading/chart.html')


class Setting(TemplateView):
    template_name = 'trading/settings.html'
    setting = None

    def get_setting(self, **kwargs):
        context = super(Setting, self).get_setting(**kwargs)
        context['setting'] = self.request.GET.get('setting')
        setting = context['setting']
        print(setting)
        if setting == 'download':
            get_nyse_data.save_nyse_tickers()
            print(context['setting'])

        return context


class Graph(TemplateView):
    template_name = 'trading/chart.html'
    ticker = None

    def get_context_data(self, **kwargs):
        context = super(Graph, self).get_context_data(**kwargs)
        context['ticker'] = self.request.GET.get('ticker')
        ticker = self.request.GET.get('ticker')

        # Calls method to create market data dataframe from sql query
        df = db.create_df(ticker)

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
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')

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
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'trading/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'account_activation_sent')
