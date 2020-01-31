from .trading.backend.fx.currency import save_currencies
from .trading.backend.fx.fx_data import save_pairs_and_data



def create_seed_data():
    save_currencies()
