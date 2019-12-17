from django.contrib import admin
from .models import Exchange, Country, Stock, MarketData, Favourites


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


class FavouriteAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Users Favourite', {'fields': ['account', 'stock']}),
    ]


admin.site.register(Country, CountryAdmin)
admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(MarketData, MarketDataAdmin)
admin.site.register(Favourites, FavouriteAdmin)
