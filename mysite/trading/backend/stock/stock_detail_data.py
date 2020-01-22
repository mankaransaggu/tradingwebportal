from ..change_calc import get_change_percent, get_change
from ..stock.stock_dates import *
from ..stock.stock_charts import create_stock_chart, create_intraday_chart, create_stock_change
from ...models import Stock


# Methods that sets all of the context variables for the detail view
def get_view_context(context):
    context['day_change'] = get_change(context['latest'].close, context['day_bef'].close)
    context['day_change_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)

    context['yest_diff'] = get_change(context['latest'].close, context['day_bef'].close)
    context['yest_diff_perc'] = get_change_percent(context['latest'].close, context['day_bef'].close)
    context['yest_vol_diff'] = get_change_percent(context['yesterday'].volume, context['day_bef'].volume)

    context['week_diff'] = get_change(context['latest'].close, context['week'].close)
    context['week_diff_perc'] = get_change_percent(context['latest'].close, context['week'].close)
    context['week_vol_diff'] = get_change_percent(context['latest'].volume, context['week'].volume)

    context['month_diff'] = get_change(context['latest'].close, context['month'].close)
    context['month_diff_perc'] = get_change_percent(context['latest'].close, context['month'].close)
    context['month_vol_diff'] = get_change_percent(context['latest'].volume, context['month'].volume)

    context['ytd_diff_perc'] = get_change_percent(context['latest'].close, context['ytd'].close)
    context['ytd_diff'] = get_change(context['latest'].close, context['ytd'].close)
    context['ytd_vol_diff'] = get_change_percent(context['latest'].volume, context['ytd'].volume)

    context['early_diff'] = get_change(context['latest'].close, context['earliest'].close)
    context['early_diff_perc'] = get_change_percent(context['latest'].close, context['earliest'].close)
    context['early_vol_diff'] = get_change_percent(context['latest'].volume, context['earliest'].volume)

    return context


def create_detail_data(stock, context):
    context['historic_graph'] = create_stock_chart(365, stock)
    context['intraday_graph'] = create_intraday_chart(stock)

    context['latest'] = get_latest(stock)
    context['yesterday'] = get_yesterday(stock)
    context['day_bef'] = get_day_before(stock)
    context['week'] = get_week(stock)
    context['month'] = get_month(stock)
    context['ytd'] = get_ytd(stock)
    context['earliest'] = get_earliest(stock)

    get_view_context(context)

    context['summary'] = create_stock_change(stock)


def get_latest_stock_details(context):
    stocks = Stock.objects.all().only('id')
    details = get_latest(stocks)

    context['stock_details'] = details
