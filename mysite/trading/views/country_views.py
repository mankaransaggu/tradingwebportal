from django.shortcuts import get_object_or_404
from django.views import generic

from mysite.trading.models import Country


class CountryListView(generic.ListView):
    template_name = 'country/country_list.html'
    model = Country

    def get_queryset(self):
        return Country.objects.all()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CountryListView, self).get_context_data(**kwargs)
        request = self.request

        return context


class CountryDetailView(generic.DetailView):
    model = Country
    template_name = 'country/country_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CountryDetailView, self).get_context_data(**kwargs)
        request = self.request
        pk = self.kwargs['pk']

        country = get_object_or_404(Country, pk=pk)


        return context