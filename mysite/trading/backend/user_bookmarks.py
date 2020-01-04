def check_is_favourite(user, stock, context):
    is_favourite = False
    if stock.favourite.filter(id=user.id).exists():
        is_favourite = True

    context['is_favourite'] = is_favourite

