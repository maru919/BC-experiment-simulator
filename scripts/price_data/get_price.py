from datetime import date, datetime as dt
from sre_compile import isstring

import pandas as pd
import yfinance as yf


class GetPriceData(object):
    """
    株価を取得するクラス
    現状 Yahoo! Finance から価格データを取得
    """

    def __init__(self) -> None:
        pass

    def get_close_price_all(self, code: str, start_date: date = None, end_date: date = None, is_local: bool = False) -> pd.core.series.Series:
        # initialize start_date_str if None
        if start_date is None or isstring(start_date):
            start_date = dt.today()

        if is_local:
            print("get data from local csv.")
            # TODO: implement local data reader

        price_df = yf.download(code, start=start_date, end=end_date, progress=False)
        price_series = price_df['Close']
        return price_series

    def get_close_price(self, code: str, date: date, is_local: bool = False) -> float:
        if code == 'JPY':
            return 1.0
        if is_local:
            print("get data from local csv.")
            return 500.0

        price_df = yf.download(code, start=date, progress=False)
        price_series = price_df['Close']
        return price_series[0]

    def get_today_close_price(self, code: str, is_local: bool = False) -> float:
        if code == 'JPY':
            return 1.0
        if is_local:
            print("get data from local csv.")
            # TODO: implement local data reader

        price_series = self.get_close_price_all(code)
        return price_series[0]

    @staticmethod
    def get_weekly_close(code: str) -> pd.core.series.Series:
        return yf.download(code, period='7d', interbal='1d', progress=False)['Close']

    def get_usdjpy_close(self, date: date, is_local: bool = False):
        if is_local:
            return 150.0
        return self.get_close_price('JPY=X', date)

    def get_usdjpy_today_close(self):
        price_series = self.get_close_price('JPY=X')
        return price_series[0]

    @staticmethod
    def get_usdjpy_weekly_close() -> pd.core.series.Series:
        return yf.download('JPY=X', period='7d', interbal='1d', progress=False)['Close']
