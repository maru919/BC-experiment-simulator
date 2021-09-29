"""
1. JCT=(N, 可変), ST=(1, 可変)
    - JCT の価値は担保に入れられた複数の有価証券の価値から算出される
    - 時価更新時には JCT の総数量は不変で、その価値が更新される
    - 取引においては JCT の授受によって自動マージンコールが行われる
1-a.
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
from pprint import pprint
import math

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
    if print_log:
        print()
    return total_value


class VariableGlobalTransaction(object):
    def __init__(self, borrower, lender, st_portfolio, init_jct_price, start_date, weight, margin_call_ratio=0.8):
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
            return {'from': self.borrower, 'to': self.lender, 'jct_num': diff, 'from_borrower': True}

        if jct_total * self.margin_call_ratio > st_total:
            diff = (jct_total * self.margin_call_ratio - st_total) / jct_price
            print(f'Margin Call! Lender needs to add {diff} or more JCT!')
            return {'from': self.lender, 'to': self.borrower, 'jct_num': diff, 'from_borrower': False}

        print(f'OK. No margin call.')
        return None

    def add_transaction_jct(self, add_num):
        self.transaction_jct_num += add_num

    def get_transaction_jct(self):
        return self.transaction_jct_num


class VariableLocalTransaction(object):
    """
    JCT可変複数
    トランザクションごとに固有の JCT を発行
    """
    def __init__(self, borrower:str, lender:str, jct_portfolio:dict, st_portfolio:dict, start_date, loan_ratio:float, print_log:bool = False) -> None:
        self.borrower = borrower
        self.lender = lender
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.loan_ratio = loan_ratio
        self.print_log = print_log
        self.logs = []
        print(f'JCT portfolio: {self.jct_portfolio}')
        print(f'ST portfolio: {self.st_portfolio}')

        self.lender_jct_num = update_portfolio_price(self.st_portfolio, start_date, print_log) * self.loan_ratio
        self.total_jct_num = update_portfolio_price(self.jct_portfolio, start_date, print_log)
        self.borrower_jct_num = self.total_jct_num - self.lender_jct_num

        if self.borrower_jct_num < 0:
            print('Initial JCT is insufficient!!')

        log = {
            'date': start_date,
            'jct_price': 1.0,
            'st_total_value': self.lender_jct_num,
            'lender_jct_total_value': self.lender_jct_num,
            'jct_total_value': self.total_jct_num,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_difference': 0
        }

        self.logs.append(log)
        pprint(log)

        print('Transaction is made.')

        # print(f'{self.lender_jct_num} JCT is handed to Lender {self.lender}')
        # print(f'Borrower {self.borrower} has {self.borrower_jct_num} JCT more.')

    def check_diff_and_margin_call(self, date):
        """
        JCT, ST それぞれの時価更新を行い、差分の JCT 口数を算出、移動する
        借り手（Borrower）の持つ JCT が不足する場合はアラートを出す
        """
        st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log)
        jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log)

        jct_price = math.floor(((jct_total_value / self.total_jct_num) * 1e6)) / 1e6

        lender_jct_total_value = self.lender_jct_num * jct_price

        jct_diff_num = math.ceil((st_total_value * self.loan_ratio - lender_jct_total_value) / jct_price)

        if jct_diff_num > 0:

        # if st_total_value * self.loan_ratio > lender_jct_total_value:
            # jct_diff_num = (st_total_value * self.loan_ratio - lender_jct_total_value) / jct_price

            if jct_diff_num > self.borrower_jct_num:
                self.lender_jct_num += self.borrower_jct_num
                self.borrower_jct_num = 0
                print('¥'*50)
                print('Borrower must add JCT!!')
                print('¥'*50)

            else:
                self.lender_jct_num += jct_diff_num
                self.borrower_jct_num -= jct_diff_num
                print('OK. JCT is moved.')

        else:
            self.lender_jct_num -= abs(jct_diff_num)
            self.borrower_jct_num += abs(jct_diff_num)
            print('OK. JCT is moved.')

        log = {
            'date': date,
            'jct_price': jct_price,
            'st_total_value': st_total_value,
            'lender_jct_total_value': lender_jct_total_value,
            'jct_total_value': jct_total_value,
            'borrower_jct_num': self.borrower_jct_num,
            'lender_jct_num': self.lender_jct_num,
            'jct_difference': jct_diff_num
        }

        self.logs.append(log)
        pprint(log)


class StableTransaction(object):
    def __init__(self, borrower, lender, st_portfolio, start_datetime, weight, margin_call_ratio=0.8):
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
        self.st_portfolio = st_portfolio.copy()
        self.start_datetime = start_datetime
        self.weight = weight
        self.margin_call_ratio = margin_call_ratio
        self.st_total_value = 0

        self.update_st_price(start_datetime)
        self.transaction_jct_num = self.st_total_value * self.weight
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

    def check_diff_and_margin_call(self):
        """
        STポートフォリオの総価値と掛け目に応じて必要JCT口数を算出し、差分のJCT口数を返す
        """
        st_total = self.st_total_value
        jct_total = self.transaction_jct_num

        if jct_total < st_total * self.margin_call_ratio:
            diff = st_total * self.margin_call_ratio - jct_total
            print(f'Margin Call! Borrower needs to add {diff} or more JCT!')
            return {'from': self.borrower, 'to': self.lender, 'jct_num': diff, 'from_borrower': True}

        if jct_total * self.margin_call_ratio > st_total:
            diff = jct_total * self.margin_call_ratio - st_total
            print(f'Margin Call! Lender needs to add {diff} or more JCT!')
            return {'from': self.lender, 'to': self.borrower, 'jct_num': diff, 'from_borrower': False}

        print(f'OK. No margin call.')
        return None

    def add_transaction_jct(self, add_num):
        self.transaction_jct_num += add_num

    def get_transaction_jct(self):
        return self.transaction_jct_num


class VariableGlobalJCT(object):
    """
    可変JCT
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


class StableJCT(object):
    """
    1JCT = 1円 で固定する場合
    """
    def __init__(self):
        self.users = {}
        self.jct_num = 0
        self.jct_price = 1.0

    def add_jct(self, user_name, jct_portfolio, date):
        usdjpy = price_getter.get_usdjpy_close(date)
        add_jct_portfolio_total = 0

        if user_name not in self.users:
            self.users[user_name] = jct_portfolio.copy()

            for code in jct_portfolio:
                num = jct_portfolio[code]['num']
                price = price_getter.get_close_price(code, date)
                if jct_portfolio[code]['is_usd']:
                    price *= usdjpy
                add_jct_portfolio_total += price * num

            self.users[user_name]['total_jct_num'] = add_jct_portfolio_total

        else:
            for code in jct_portfolio:
                num = jct_portfolio[code]['num']
                if code in self.users[user_name]:
                    self.users[user_name][code]['num'] += num
                else:
                    self.users[user_name][code] = jct_portfolio[code].copy()
                price = price_getter.get_close_price(code, date)
                if jct_portfolio[code]['is_usd']:
                    price *= usdjpy
                add_jct_portfolio_total += price * num

            self.users[user_name]['total_jct_num'] += add_jct_portfolio_total

        self.jct_num += add_jct_portfolio_total

    def get_change(self, date):
        """
        JCTのポートフォリオに含まれる各有価証券について時価を更新し、JCTの価値を固定するための変化分を算出
        """
        usdjpy = price_getter.get_usdjpy_close(date)
        changes = {}

        for user in list(self.users.keys()):
            new_jct_total_value = 0

            for code in list(self.users[user].keys()):
                if code == 'total_jct_num':
                    continue

                num = self.users[user][code]['num']
                new_price = price_getter.get_close_price(code, date)

                if self.users[user][code]['is_usd']:
                    new_price *= usdjpy

                print(f'{code}: {new_price}')

                self.users[user][code]['price'] = new_price
                new_jct_total_value += new_price * num
            changes[user] = new_jct_total_value - self.users[user]['total_jct_num']

        return changes

    def exec_change_num(self, user, change_num):
        self.users[user]['total_jct_num'] += change_num

    def get_jct_num(self):
        return self.jct_num

    def move_jct(self, _from, to, num):
        print(f'move {num} from {_from} to {to}')
        self.users[_from]['total_jct_num'] -= num
        self.users[to]['total_jct_num'] += num
        print(self.users)
