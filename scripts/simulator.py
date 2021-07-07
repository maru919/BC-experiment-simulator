class Transaction(object):
    def __init__(self, jct_portfolio, st_portfolio, start_datetime_str, end_datetime_str, loan_ratio):
        """
        Args:
            jct_portfolio (list): portfolio of jct, ex:
                [
                    {
                        'id': 'MSFT',
                        'price': 249.68,
                        'num': 10000,
                        'is_usd': True
                    },
                    {
                        'id': '3967',
                        'price': 15490,
                        'num': 10000,
                        'is_usd': False
                    },
                    {
                        'id': '6758',
                        'price': 10785,
                        'num': 10000,
                        'is_usd': False
                    },
                ]
            st_portfolio (list): portfolio of st
            start_datetime_str (str): start datetime of the transaction
            end_datetime_str (str): end datetime of the transaction
            loan_ratio (float): loan ratio
        """
        self.jct_portfolio = jct_portfolio
        self.st_portfolio = st_portfolio
        self.start_datetime = start_datetime_str
        self.end_datetime  = end_datetime_str
        self.loan_ratio = loan_ratio
        self.yen_per_usd = self.update_yen_per_usd()

    def update_yen_per_usd():
        """
        円/ドルを取得し更新する
        """
        pass

    def update_price_all(self):
        """
        JCT、STのポートフォリオに含まれる各有価証券について時価を更新する
        """
        pass

    def check_value_diff(self):
        """
        STポートフォリオの総価値と掛け目に応じて必要JCT口数を算出し、差分のJCT口数を返す
        """
        pass

    def margin_call(self):
        """
        マージンコールを発生させる
        """
        pass

    def settle(self):
        """
        決済処理を行う
        """
        pass
