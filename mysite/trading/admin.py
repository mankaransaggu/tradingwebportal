from django.contrib import admin
from .models import Exchange, Country, Position, Stock, MarketData


class CountryAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Country', {'fields': ['code', 'name']}),
    ]


class ExchangeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Exchange', {'fields': ['code', 'name', 'country']}),
    ]


class StockAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Stock', {'fields': ['ticker', 'name', 'exchange']}),
    ]


class MarketDataAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Instrument', {'fields': ['ticker', 'date']}),
        ('Data', {'fields': ['high',  'low', 'open', 'close', 'volume', 'adj_close']})
    ]


admin.site.register(Country, CountryAdmin)
admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(MarketData, MarketDataAdmin)
