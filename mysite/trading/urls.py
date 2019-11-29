from django.urls import path, include, re_path
from django.views.generic import TemplateView
from .views import Graph, Settings

from . import views

urlpatterns = [
    path('', views.home, name='search'),
    path('search/', Graph.as_view(), name='market_search'),
    path('settings/', Settings.as_view(), name='settings'),
]
