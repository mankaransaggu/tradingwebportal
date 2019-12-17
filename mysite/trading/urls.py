from django.urls import path, include, re_path
from . import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('equities/', views.StocksView.as_view(), name='equites'),
    path('equity/<int:pk>/', views.StockView.as_view(), name='equity'),
    path('exchanges/', views.ExchangesView.as_view(), name='exchanges'),
    path('exchange/<int:pk>/', views.ExchangeStocksView.as_view(), name='exchange'),


    path('signup/', views.signup, name='signup'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('account/', views.account, name='account'),
    path('settings/', views.Setting.as_view(), name='settings'),



    re_path(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
]
