"""
1. JCT=(N, 可変), ST=(1, 可変) [On Going]
    - JCT の価値は担保に入れられた複数の有価証券の価値から算出される
    - 時価更新時には JCT の総数量は不変で、その価値が更新される
    - 取引においては JCT の授受によって自動マージンコールが行われる


1-a.(Deprecated!!)
VariableGlobalTransaction()
GlobalJCT()
    - JCT はグローバル（あらゆる取引においても唯一の価値）
    - 参加者が担保に入れた有価証券全てからその価値を算出し、全員が同じものを共有
    - 全体でのポートフォリオを把握したうえで時価を更新
    - 参加者ごとには数量を把握
1-b.
VariableLocalTransaction()
    - JCT は取引ごとに独立のもの
    - 取引開始時に、借り手は有価証券を担保にそれぞれ JCT を発行
    - 参加者ごとのポートフォリオ、数量等を把握しておけばよいため、取引ごとのみのクラスで完結する

2. JCT=(N, 固定), ST=(1, 可変)
StableTransaction()
StableJCT()
    - 時価更新時には JCT の価値は固定（1JCT = 1円）で、その数量が調整される
    - 担保の有価証券の価値が減少した場合には対応する分の JCT を削除、増加した場合には追加で JCT を発行する
    - 発行者ごとに数量を管理

3. JCT=(1, 可変), ST=(1, 可変)
VariableRespectiveTransaction()
    - JCT も ST と同様に有価証券ごとに1種類ずつトークンを発行する
    - 取引期間中のトークンの授受においては、事前に担保とする JCT に優先度をつけておき、優先度の高いものから授受していく
"""
import copy
import math
from pprint import pprint

from .price_data.get_price import GetPriceData

price_getter = GetPriceData()


def update_portfolio_price(portfolio, date, print_log=False):
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


class VariableLocalTransaction(object):
    """
    JCT可変複数
    トランザクションごとに固有のJCTを発行
    """

    def __init__(self, jct_portfolio: dict, st_portfolio: dict, start_date, borrower: str = 'Borrower(A)', lender: str = 'Lender(B)',
                 borrower_loan_ratio: float = 1.0, lender_loan_ratio: float = 1.0, print_log: bool = False, auto_deposit: bool = False) -> None:
        self.borrower = borrower
        self.lender = lender
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = borrower_loan_ratio
        self.lender_loan_ratio = lender_loan_ratio
        self.print_log = print_log
        self.auto_deposit = auto_deposit
        self.logs = []
        print(f'JCT portfolio: {self.jct_portfolio}')
        print(f'ST portfolio: {self.st_portfolio}')

        st_total_value = update_portfolio_price(self.st_portfolio, start_date, print_log)
        self.lender_jct_num = math.ceil(st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio)
        self.total_jct_num = math.floor(update_portfolio_price(self.jct_portfolio, start_date, print_log))
        self.borrower_jct_num = self.total_jct_num - self.lender_jct_num

        if self.borrower_jct_num < 0:
            raise ValueError(f'Initial JCT is insufficient!!\nborrower_jct_num: {self.borrower_jct_num}')

        log = {
            'date': start_date,
            'jct_price': 1.0,
            'st_total_value': st_total_value,
            'jct_total_value': self.total_jct_num,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_difference': 0,
            'auto_deposit': False
        }

        self.logs.append(log)

        print('Transaction is created.')
        if print_log:
            pprint(log)

    def check_diff_and_margin_call(self, date):
        """
        JCT, STそれぞれの時価更新を行い、差分のJCT口数を算出、移動する
        JCTの裏付けとなる担保が不足する場合はアラートを出す
        """
        st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log)
        jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log)

        jct_price = math.floor(((jct_total_value / self.total_jct_num) * 1e6)) / 1e6

        lender_jct_total_value = self.lender_jct_num * jct_price

        jct_diff_num = math.ceil(((st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio) - lender_jct_total_value) / jct_price)

        necessary_deposit = jct_diff_num > 0 and jct_diff_num > self.borrower_jct_num
        if necessary_deposit:
            if not self.auto_deposit:
                raise ValueError(f'WARNING: {self.borrower} must add JCT!!')

            # 自動で不足分の現金を補填する
            additional_deposit = math.ceil((jct_diff_num - self.borrower_jct_num) * jct_price)
            print(f'Additional deposit! {additional_deposit} JPY is added.')
            print('*' * 50)
            print('*' * 50)
            self.jct_portfolio['JPY']['num'] += additional_deposit
            self.lender_jct_num += jct_diff_num
            self.total_jct_num += jct_diff_num - self.borrower_jct_num
            self.borrower_jct_num = 0

        else:
            self.lender_jct_num += jct_diff_num
            self.borrower_jct_num -= jct_diff_num

        log = {
            'date': date,
            'jct_price': jct_price,
            'st_total_value': st_total_value,
            'jct_total_value': jct_total_value,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_difference': jct_diff_num,
            'auto_deposit': necessary_deposit
        }

        self.logs.append(log)
        if self.print_log:
            print('OK. JCT is moved.')
            pprint(log)


class StableTransaction(object):
    """
    JCT固定複数
    JCTの価格が常に1円になるよう抹消・追加発行によってJCTの数量を調整
    """

    def __init__(self, jct_portfolio: dict, st_portfolio: dict, start_date, borrower: str = 'Borrower(A)', lender: str = 'Lender(B)',
                 borrower_loan_ratio: float = 1.0, lender_loan_ratio: float = 1.0, print_log: bool = False, auto_deposit: bool = False) -> None:
        print(jct_portfolio, st_portfolio, start_date)
        self.borrower = borrower
        self.lender = lender
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = borrower_loan_ratio
        self.lender_loan_ratio = lender_loan_ratio
        self.print_log = print_log
        self.auto_deposit = auto_deposit
        self.logs = []
        pprint(f'JCT portfolio: {self.jct_portfolio}')
        pprint(f'ST portfolio: {self.st_portfolio}')

        st_total_value = update_portfolio_price(self.st_portfolio, start_date, print_log)
        self.lender_jct_num = math.ceil(st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio)
        self.total_jct_num = math.floor(update_portfolio_price(self.jct_portfolio, start_date, print_log))
        self.borrower_jct_num = self.total_jct_num - self.lender_jct_num

        if self.borrower_jct_num < 0:
            raise ValueError('Initial JCT is insufficient!!')

        log = {
            'date': start_date,
            'st_total_value': self.lender_jct_num,
            'jct_total_num': self.total_jct_num,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_diff_num': 0,
            'moved_jct_num': 0,
            'auto_deposit': False
        }
        self.logs.append(log)

        print('Transaction is created.')
        if print_log:
            pprint(log)

    def check_diff_and_margin_call(self, date):
        """
        JCT, STそれぞれの時価更新を行い、JCTについては価値が一円固定になるように一部トークンの抹消、追加発行を行う
        JCTの裏付けとなる担保が不足する場合はアラートを出す
        """
        st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log)
        jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log)

        jct_diff_num = math.ceil(jct_total_value) - self.total_jct_num
        auto_deposit = False
        if jct_diff_num < 0 and (self.borrower_jct_num + jct_diff_num) < 0:
            if not self.auto_deposit:
                raise ValueError(f'WARNING: {self.borrower} must add enough collateral for more JCT.')

            # 自動で不足分の現金を補填する
            auto_deposit = True
            additional_deposit = abs(self.borrower_jct_num + jct_diff_num)
            print(f'Additional deposit! {additional_deposit} JPY is added.')
            self.jct_portfolio['JPY']['num'] += additional_deposit
            self.total_jct_num += additional_deposit
            self.borrower_jct_num += additional_deposit

        self.total_jct_num += jct_diff_num
        self.borrower_jct_num += jct_diff_num

        st_diff_num = math.ceil(st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio) - self.lender_jct_num
        if st_diff_num > self.borrower_jct_num:
            if not self.auto_deposit:
                raise ValueError(f'WARNING: {self.borrower} must add enough collateral for more JCT.')

            # 自動で不足分の現金を補填する
            auto_deposit = True
            additional_deposit = abs(st_diff_num - self.borrower_jct_num)
            print(f'Additional deposit! {additional_deposit} JPY is added.')
            self.jct_portfolio['JPY']['num'] += additional_deposit
            self.total_jct_num += additional_deposit
            self.borrower_jct_num = 0
            self.lender_jct_num += st_diff_num
        else:
            self.lender_jct_num += st_diff_num
            self.borrower_jct_num -= st_diff_num

        log = {
            'date': date,
            'st_total_value': st_total_value,
            'jct_total_num': self.total_jct_num,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_diff_num': jct_diff_num,
            'moved_jct_num': st_diff_num,
            'auto_deposit': auto_deposit
        }

        self.logs.append(log)
        if self.print_log:
            print('OK. JCT is properly issued or deleted and moved.')
            pprint(log)


class VariableGlobalTransaction(object):
    """
    可変JCTグローバル
    WARNING: Deprecated! Not refactored.
    """

    def __init__(self, borrower, lender, st_portfolio,
                 init_jct_price, start_date, weight, margin_call_ratio=0.8):
        """
        Args: Transaction info
            st_portfolio (list): portfolio of st
            init_jct_price (float): jct price at start
            start_datetime_str (str): start datetime of the transaction
            loan_weight (float): loan weight
            margin_call_ratio (float): margin call automatically occurs when collateral value go under this ratio of total st_portfolio value
        """
        self.borrower = borrower
        self.lender = lender
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.start_date = start_date
        self.weight = weight
        self.margin_call_ratio = margin_call_ratio
        self.st_total_value = 0

        self.update_st_price(start_date)
        self.transaction_jct_num = self.st_total_value * self.weight / init_jct_price
        print(f'Initial jct num is {self.transaction_jct_num}.')

    def update_st_price(self, date_str):
        """
        STのポートフォリオに含まれる各有価証券について時価を更新する
        """
        usdjpy = price_getter.get_usdjpy_close(date_str)
        st_total = 0
        for code in list(self.st_portfolio.keys()):
            new_price = price_getter.get_close_price(code, date_str)
            if self.st_portfolio[code]['is_usd']:
                new_price *= usdjpy
            self.st_portfolio[code]['price'] = new_price
            # print(code, ': ', new_price)
            st_total += new_price * self.st_portfolio[code]['num']
        self.st_total_value = st_total

    def check_diff_and_margin_call(self, jct_price):
        """
        STポートフォリオの総価値と掛け目に応じて必要JCT口数を算出し、差分のJCT口数を返す
        """
        st_total = self.st_total_value
        jct_total = self.transaction_jct_num * jct_price
        print('jct_total:', jct_total)
        print('st_total:', st_total)

        if jct_total < st_total * self.margin_call_ratio:
            diff = (st_total * self.margin_call_ratio - jct_total) / jct_price
            print(f'Margin Call! Borrower needs to add {diff} or more JCT!')
            return {'from': self.borrower, 'to': self.lender,
                    'jct_num': diff, 'from_borrower': True}

        if jct_total * self.margin_call_ratio > st_total:
            diff = (jct_total * self.margin_call_ratio - st_total) / jct_price
            print(f'Margin Call! Lender needs to add {diff} or more JCT!')
            return {'from': self.lender, 'to': self.borrower,
                    'jct_num': diff, 'from_borrower': False}

        print('OK. No margin call.')
        return None

    def add_transaction_jct(self, add_num):
        self.transaction_jct_num += add_num

    def get_transaction_jct(self):
        return self.transaction_jct_num


class VariableGlobalJCT(object):
    """
    可変JCT
    WARNING: Deprecated! Not refactored.
    """

    def __init__(self):
        self.jct_portfolio = {}
        self.users = {}
        self.jct_num = 0
        self.jct_price = 0

    def add_jct(self, user_name, jct_portfolio, date_str):
        """
        Args:
            user_name (str): user name
            jct_portfolio (dict): portfolio of jct, ex:
                {
                    'MSFT': {
                        'num': 10000,
                        'is_usd': True
                    },
                    '3967.T': {
                        'num': 10000,
                        'is_usd': False
                    },
                    '6578.T': {
                        'num': 10000,
                        'is_usd': False
                    },
                }
        """
        usdjpy = price_getter.get_usdjpy_close(date_str)
        add_jct_portfolio_total = 0

        for code in jct_portfolio:
            num = jct_portfolio[code]['num']
            if code in self.jct_portfolio:
                self.jct_portfolio[code]['num'] += num
            else:
                self.jct_portfolio[code] = jct_portfolio[code].copy()

            price = price_getter.get_close_price(code, date_str)
            if jct_portfolio[code]['is_usd']:
                price *= usdjpy
            add_jct_portfolio_total += price * num

        if self.jct_num == 0:
            add_num = add_jct_portfolio_total
            self.jct_price = 1.0
        else:
            add_num = add_jct_portfolio_total / self.jct_price
        # print('add_num:', add_num)
        self.jct_num += add_num

        if user_name not in self.users:
            self.users[user_name] = jct_portfolio.copy()
            self.users[user_name]['total_jct_num'] = add_num
        else:
            self.users[user_name]['total_jct_num'] += add_num
            for code in jct_portfolio:
                if code in self.users[user_name]:
                    self.users[user_name][code]['num'] += jct_portfolio[code]['num']
                else:
                    self.users[user_name][code] = jct_portfolio[code]

    def update_price(self, date_str):
        """
        JCTのポートフォリオに含まれる各有価証券について時価を更新する
        """
        usdjpy = price_getter.get_usdjpy_close(date_str)
        new_jct_total_value = 0

        for code in self.jct_portfolio:
            num = self.jct_portfolio[code]['num']
            new_price = price_getter.get_close_price(code, date_str)
            if self.jct_portfolio[code]['is_usd']:
                new_price *= usdjpy

            print(f'{code}: {new_price}')
            self.jct_portfolio[code]['price'] = new_price
            new_jct_total_value += new_price * num

        self.jct_price = new_jct_total_value / self.jct_num

    def get_jct_price(self):
        return self.jct_price

    def get_jct_num(self):
        return self.jct_num

    def move_jct(self, _from, to, num):
        print(f'move {num} from {_from} to {to}')
        self.users[_from]['total_jct_num'] -= num
        self.users[to]['total_jct_num'] += num
        print(self.users)
