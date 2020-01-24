from django.contrib import admin
from . models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    pass


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    pass


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    pass


@admin.register(StockPriceData)
class StockPriceDataAdmin(admin.ModelAdmin):
    pass


@admin.register(FX)
class FXAdmin(admin.ModelAdmin):
    pass


@admin.register(FXPriceData)
class FXPriceDataAdmin(admin.ModelAdmin):
    pass


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    pass


