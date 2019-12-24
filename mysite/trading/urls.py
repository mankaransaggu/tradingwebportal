from django.urls import path, include, re_path
from . import views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('equities/', views.StocksView.as_view(), name='equites'),
    path('equity/<int:pk>/', views.StockView.as_view(), name='equity'),
    path('<int:id>/favourite_equity/', views.favourite_equity, name='favourite_equity'),
    path('exchanges/', views.ExchangesView.as_view(), name='exchanges'),
    path('exchange/<int:pk>/', views.ExchangeStocksView.as_view(), name='exchange'),


    path('signup/', views.signup, name='signup'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('account/', views.AccountView.as_view(), name='account'),
    path('account/edit/', views.edit_account, name='edit_account'),
    path('change-password/', views.change_password, name='change_password'),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),

    path('settings/', views.Setting.as_view(), name='settings'),

    path('open-position/', views.OpenPositionForm.as_view(), name='open_position'),

    re_path(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            views.activate, name='activate'),
]
