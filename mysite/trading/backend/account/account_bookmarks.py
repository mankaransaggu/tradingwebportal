from ...models import Stock


def check_is_favourite(user, stock, context):
    is_favourite = False
    if stock.favourite.filter(id=user.id).exists():
        is_favourite = True

    context['is_favourite'] = is_favourite


# Gets all of the current user favourites
def get_user_favourites(user, context):
    if user.is_authenticated:
        favourites = user.favourite_stock.all()
        context['favourites'] = favourites
    else:
        return None


# Method for checking what stocks for a certain exchange in a list are user favourites
def check_exchange_stock(user, exchange, context):
    favourites = Stock.objects.filter(favourite__pk=user.pk, exchange=exchange).only('id', 'ticker')
    context['favourite_list'] = favourites


# Method for checking what stocks displayed in a list are user favourites
def check_stock_list(user, context):
    favourites = Stock.objects.filter(favourite__pk=user.pk).only('id', 'ticker')
    context['favourite_list'] = favourites


# Method to get the number of stocks on an exchange the user has bookmarked
def favourite_exchange_stocks(user, exchange, context):
    favourites = Stock.objects.filet(favourite__pk=user.pk, exchange=exchange).count()
    print(favourites)
    context['exchange_favourites'] = favourites
