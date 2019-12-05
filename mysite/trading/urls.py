from django.urls import path, include, re_path
from django.views.generic import TemplateView
from .views import Graph, Setting
from . import views as trading_views

from . import views

urlpatterns = [
    path('', views.home, name='search'),
    path('search/', Graph.as_view(), name='market_search'),
    path('signup/', views.signup, name='signup'),
    path('settings/', Setting.as_view(), name='settings'),
    re_path(r'^account_activation_sent/$', trading_views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
]
