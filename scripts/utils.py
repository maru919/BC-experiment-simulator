from datetime import date
import math
from operator import is_
from .price_data.get_price import GetPriceData

price_getter = GetPriceData()


def update_portfolio_price(portfolio, date: date, print_log: bool=False, is_dummy_data: bool=False) -> int:
    """
    ポートフォリオに含まれる各有価証券について時価を更新し、トータルの価値を返す
    """
    usdjpy = price_getter.get_usdjpy_close(date, is_local=is_dummy_data)
    total_value = 0
    if print_log:
        print(f'{date}: Price updating...')

    for code in list(portfolio.keys()):
        new_price = price_getter.get_close_price(code, date, is_local=is_dummy_data)
        if portfolio[code]['is_usd']:
            new_price *= usdjpy
        new_price = math.floor(new_price * 10) / 10
        portfolio[code]['price'] = new_price

        if print_log:
            print(f'{code}: {new_price}')

        total_value += new_price * portfolio[code]['num']

    return total_value
