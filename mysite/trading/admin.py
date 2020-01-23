from django.contrib import admin
from . models import *


class CurrencyAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Currency', {'fields': ['code', 'name']}),
    ]


class CountryAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Country', {'fields': ['code', 'name', 'currency']}),
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


class StockDataAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Instrument', {'fields': ['stock', 'timestamp']}),
        ('Data', {'fields': ['high',  'low', 'open', 'close', 'volume', 'adj_close']})
    ]


class FXAdmin(admin.ModelAdmin):
    fieldsets = [
        ('FX', {'fields': ['code', 'from_currency', 'to_currency']}),
    ]


class FXDataAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Currencies', {'fields': ['currency_pair', 'timestamp']}),
        ('Data', {'fields': ['high', 'low', 'open', 'close', 'volume']})
    ]


class PositionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Account Positions', {'fields': ['open_date', 'close_date', 'open', 'account']}),
        ('Position Instrument', {'fields': ['stock', 'fx']}),
        ('Position Details', {'fields': ['open_price', 'close_price', 'direction', 'quantity', 'result']}),
    ]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Country, CountryAdmin)

admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(Instrument, InstrumentAdmin)

admin.site.register(Stock, StockAdmin)
admin.site.register(StockPriceData, StockDataAdmin)

admin.site.register(FX, FXAdmin)
admin.site.register(FXPriceData, FXDataAdmin)

admin.site.register(Position, PositionAdmin)
