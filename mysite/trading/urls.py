from django.urls import path, include, re_path
from django.views.generic import TemplateView
from .views import Graph, Setting
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', Graph.as_view(), name='market_search'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('settings/', Setting.as_view(), name='settings'),


    re_path(r'^account_activation_sent/$', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
]
