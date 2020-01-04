from django.contrib import admin
from .models import Exchange, Country, Stock, StockData, Position, Currency, Instrument


class CurrencyAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Currency', {'fields': ['code', 'name', 'base']}),
        ('Value', {'fields': ['rate']}),
    ]


class CountryAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Country', {'fields': ['code', 'name']}),
    ]


class ExchangeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Exchange', {'fields': ['code', 'name', 'country']}),
    ]


class InstrumentAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Instrument', {'fields': ['code', 'name', 'description']}),
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


class PositionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Account Positions', {'fields': ['open_date', 'close_date', 'ticker', 'position_state', 'account']}),
        ('Position Details', {'fields': ['open_price', 'close_price', 'direction', 'quantity', 'result']}),
    ]


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(StockData, MarketDataAdmin)
admin.site.register(Position, PositionAdmin)
