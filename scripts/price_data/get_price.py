from datetime import datetime as dt
import pandas as pd
import yfinance as yf

class GetPriceData(object):
    """
    株価を取得するクラス
    現状 Yahoo! Finance から価格データを取得
    """
    def __init__(self) -> None:
        pass

    def get_close_price_all(self, code: str, start_date_str=None, end_date_str=None) -> pd.core.series.Series:
        # initialize start_date_str if None
        if start_date_str is None:
            dt_now = dt.now()
            start_date_str = dt_now.strftime('%Y-%m-%d')

        price_df = yf.download(code, start=start_date_str, end=end_date_str, progress=False)
        price_series = price_df['Close']
        return price_series

    def get_close_price(self, code: str, date_str) -> float:
        if code == 'JPY':
            return 1.0
        price_df = yf.download(code, start=date_str, progress=False)
        price_series = price_df['Close']
        return price_series[0]

    def get_today_close(self, code: str) -> float:
        if code == 'JPY':
            return 1.0
        price_series = self.get_close_price_all(code)
        return price_series[0]

    @staticmethod
    def get_weekly_close(code:str) -> pd.core.series.Series:
        return yf.download(code, period='7d', interbal='1d', progress=False)['Close']

    def get_usdjpy_close(self, date_str):
        return self.get_close_price('JPY=X', date_str)

    def get_usdjpy_today_close(self):
        price_series = self.get_close_price('JPY=X')
        return price_series[0]

    @staticmethod
    def get_usdjpy_weekly_close() -> pd.core.series.Series:
        return yf.download('JPY=X', period='7d', interbal='1d', progress=False)['Close']
