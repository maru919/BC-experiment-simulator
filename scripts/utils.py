import math
from .price_data.get_price import GetPriceData

price_getter = GetPriceData()


def update_portfolio_price(portfolio, date, print_log=False) -> int:
    """
    ポートフォリオに含まれる各有価証券について時価を更新し、トータルの価値を返す
    """
    usdjpy = price_getter.get_usdjpy_close(date)
    total_value = 0
    if print_log:
        print(f'{date}: Price updating...')

    for code in list(portfolio.keys()):
        new_price = price_getter.get_close_price(code, date)
        if portfolio[code]['is_usd']:
            new_price *= usdjpy
        new_price = math.floor(new_price * 10) / 10
        portfolio[code]['price'] = new_price

        if print_log:
            print(f'{code}: {new_price}')

        total_value += new_price * portfolio[code]['num']

    return total_value
