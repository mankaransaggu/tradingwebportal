from django.test import TestCase
from .models import Country, Exchange, Stock, MarketData


class CountryTestCase(TestCase):
    def setUp(self):
        Country.objects.create(code="TEST", name="Test Country")

    def test_country(self):
        country = Country.objects.get(code="TEST")
        self.assertEqual(country.code, "TEST")


class StockTestCase(TestCase):
    def setup(self):
        Stock.objects.create(ticker="TEST", name="Test Stock")

