from mysite.trading.models import Position


def get_positions(user, stock_pk, context):
    open_positions = Position.objects.filter(account_id=user.pk, instrument__id=stock_pk, open=True)
    close_positions = Position.objects.filter(account_id=user.pk, instrument__id=stock_pk, open=False)

    context['open_positions'] = open_positions
    context['close_positions'] = close_positions