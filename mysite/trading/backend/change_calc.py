# Gets the change between two dates data in percent
def get_change_percent(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100
    except ZeroDivisionError:
        return 0


# Gets the change between two dates data
def get_change(current, previous):
    return current - previous
