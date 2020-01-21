from ...models import Position


def get_stock_positions(user, stock, context):
    open_positions = Position.objects.filter(account_id=user.pk, stock=stock, open=True)
    close_positions = Position.objects.filter(account_id=user.pk, stock=stock, open=False)

    context['open_positions'] = open_positions
    context['close_positions'] = close_positions


def get_open_positions(user, context):
    if user.is_authenticated:
        user = user
        open_positions = Position.objects.filter(account=user, open=True).order_by('-open_date')
        context['open_positions'] = open_positions
    else:
        return None


def get_closed_positions(user, context):
    if user.is_authenticated:
        closed_positions = Position.objects.filter(account=user, open=False).order_by('-close_date')
        context['closed_positions'] = closed_positions
    else:
        return None
