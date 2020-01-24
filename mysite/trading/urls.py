from django.urls import path, include, re_path
from . import views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    path('stock-list/', views.StocksView.as_view(), name='stock_list'),
    path('stock/<int:pk>/', views.StockDetailView.as_view(), name='stock'),
    path('favourite-stock/<int:id>/', views.favourite_stock, name='favourite_stock'),

    path('exchange-list/', views.ExchangeListView.as_view(), name='exchange_list'),
    path('exchange/<int:pk>/', views.ExchangeDetailView.as_view(), name='exchange'),

    path('currency-list/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currency/<int:pk>/', views.CurrencyDetailView.as_view(), name='currency'),
    path('fx_pair/<int:pk>/', views.FXDetailView.as_view(), name='fx_pair'),

    #Account
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('account/', views.AccountView.as_view(), name='account'),
    path('account/edit/', views.edit_account, name='edit_account'),
    path('change-password/', views.change_password, name='change_password'),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    re_path(r'^verify/(?P<uuid>[a-z0-9\-]+)/', views.verify, name='verify'),

    path('search/', views.SearchView.as_view(), name='search'),
    path('settings/', views.Setting.as_view(), name='settings'),

    path('open-position/', views.OpenPositionForm.as_view(), name='open_position'),
    path('open-position/<int:id>/', views.OpenPositionForm.as_view(), name='open_position'),
    path('close-position/<int:id>/', views.close_position, name='close_position'),


]
