from django.urls import path, include, re_path
from django.views.generic import TemplateView
from .views import Setting, Search
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', Search.as_view(), name='market_search'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('account/', views.account, name='account'),
    path('settings/', Setting.as_view(), name='settings'),
    path('equities/', views.stock_list, name='equities'),
    path('exchanges/', views.exchange_list, name='exchanges'),
    path('exchange/', views.exchange_stocks, name='exchange'),


    re_path(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
]
