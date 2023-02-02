"""
シミュレーションを実行するためのクラス
"""

import copy
from datetime import date, timedelta
import math
from pprint import pprint
from typing import Dict

from .utils import update_portfolio_price

from .types import PortfolioItem, PortfolioWithPriorityItem, TransactionOption
from .variable_local import AutoAdjustmentTransactionSingle, AutoAdjustmentTransactionMulti


class ExecuteAutoAdjustmentTransactionSingle(AutoAdjustmentTransactionSingle):
    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: date, end_date: date, options: TransactionOption) -> None:
        self.borrower = options['borrower'] if 'borrower' in options else "Borrower(A)"
        self.lender = options['lender'] if 'lender' in options else 'Lender(B)'
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = options['borrower_loan_ratio'] if 'borrower_loan_ratio' in options else 1.0
        self.lender_loan_ratio = options['lender_loan_ratio'] if 'lender_loan_ratio' in options else 1.0
        self.print_log = options['print_log'] if 'print_log' in options else False
        self.auto_deposit = options['auto_deposit'] if 'auto_deposit' in options else True
        self.is_dummy_data = options['is_dummy_data'] if 'is_dummy_data' in options else False
        self.is_reverse = options['is_reverse'] if 'is_reverse' in options else False
        self.is_manual = options['is_manual'] if 'is_manual' in options else False
        self.margin_call_threshold = options['margin_call_threshold'] if 'margin_call_threshold' in options else 0.0
        self.collateral_portfolio: Dict[str, PortfolioWithPriorityItem] = {}
        self.logs: Dict[str, list] = {}
        self.start_date = start_date

        pprint(f'JCT portfolio: {self.jct_portfolio}')
        pprint(f'ST portfolio: {self.st_portfolio}')

        def date_range():
            for n in range(int((end_date - start_date).days) - 1):
                yield start_date + timedelta(n + 1)

        # 初日は初期化処理を含むため、2日目以降のgeneratorを作成
        self.date_range = date_range

        self.initialize()

    def initialize(self):
        st_total_value = update_portfolio_price(self.st_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        jct_total_value = update_portfolio_price(self.jct_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
        self.necessary_collateral_value = collateral_total_value

        for code, collateral in sorted(self.jct_portfolio.items(), key=lambda x: x[1]['priority'], reverse=True):  # type: ignore
            pprint(f'{code}: {collateral}')
            collateral_value = collateral['price'] * collateral['num']
            if collateral_value >= collateral_total_value:
                collateral_num = math.ceil(collateral_total_value / collateral['price'])

                if (collateral_num > self.jct_portfolio[code]['num']):
                    print("絶妙に足りない場合")
                    continue

                self.collateral_portfolio[code] = {
                    'num': collateral_num,
                    'is_usd': collateral['is_usd'],
                    'price': collateral['price'],
                    'priority': collateral['priority']
                }
                self.jct_portfolio[code]['num'] -= collateral_num

                collateral_total_value = 0
                print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                break

            # to next collateral
            self.collateral_portfolio[code] = {
                'num': collateral['num'],
                'is_usd': collateral['is_usd'],
                'price': collateral['price'],
                'priority': collateral['priority']
            }
            collateral_total_value -= collateral['price'] * collateral['num']
            self.jct_portfolio[code]['num'] = 0

        if collateral_total_value > 0:
            raise ValueError(f'Initial JCT is insufficient!! {self.jct_portfolio}')

        collateral_sum = update_portfolio_price(self.collateral_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        self.logs['date'] = [self.start_date]
        self.logs['st_total_value'] = [st_total_value]
        self.logs['jct_total_value'] = [jct_total_value]
        self.logs['jct_portfolio'] = [copy.deepcopy(self.jct_portfolio)]
        self.logs['collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]
        self.logs['collateral_sum'] = [collateral_sum]
        self.logs['necessary_collateral_value'] = [self.necessary_collateral_value]
        self.logs['lender_additional_issue'] = [False]
        self.logs['borrower_additional_issue'] = [False]
        self.logs['has_done_margincall'] = [True]

        self.initial_collateral_portfolio = copy.deepcopy(self.collateral_portfolio)
        self.logs['initial_collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]

        print('Transaction is created.')
        if self.print_log:
            pprint(self.logs)

    def execute(self):
        for _date in self.date_range():
            print("@" * 80)
            print(_date)
            self.check_diff_and_margin_call(_date)
            print("@" * 80)

        print("Finished!!!!")

        return self.logs


class ExecuteAutoAdjustmentTransactionMulti(AutoAdjustmentTransactionMulti):
    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: date, end_date: date, options: TransactionOption) -> None:
        self.borrower = options['borrower'] if 'borrower' in options else "Borrower(A)"
        self.lender = options['lender'] if 'lender' in options else 'Lender(B)'
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = options['borrower_loan_ratio'] if 'borrower_loan_ratio' in options else 1.0
        self.lender_loan_ratio = options['lender_loan_ratio'] if 'lender_loan_ratio' in options else 1.0
        self.print_log = options['print_log'] if 'print_log' in options else False
        self.auto_deposit = options['auto_deposit'] if 'auto_deposit' in options else True
        self.is_dummy_data = options['is_dummy_data'] if 'is_dummy_data' in options else False
        self.is_reverse = options['is_reverse'] if 'is_reverse' in options else False
        self.margin_call_threshold = options['margin_call_threshold'] if 'margin_call_threshold' in options else 0.0
        self.collateral_portfolio: Dict[str, PortfolioWithPriorityItem] = {}
        self.logs: Dict[str, list] = {}
        self.start_date = start_date

        pprint(f'JCT portfolio: {self.jct_portfolio}')
        pprint(f'ST portfolio: {self.st_portfolio}')

        def date_range():
            for n in range(int((end_date - start_date).days) - 1):
                yield start_date + timedelta(n + 1)

        # 初日は初期化処理を含むため、2日目以降のgeneratorを作成
        self.date_range = date_range

        self.initialize()

    def initialize(self):
        st_total_value = update_portfolio_price(self.st_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        jct_total_value = update_portfolio_price(self.jct_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
        self.necessary_collateral_value = collateral_total_value

        for code, collateral in sorted(self.jct_portfolio.items(), key=lambda x: x[1]['priority'], reverse=True):  # type: ignore
            pprint(f'{code}: {collateral}')
            collateral_value = collateral['price'] * collateral['num']
            if collateral_value >= collateral_total_value:
                collateral_num = math.ceil(collateral_total_value / collateral['price'])

                if (collateral_num > self.jct_portfolio[code]['num']):
                    print("絶妙に足りない場合")
                    continue

                self.collateral_portfolio[code] = {
                    'num': collateral_num,
                    'is_usd': collateral['is_usd'],
                    'price': collateral['price'],
                    'priority': collateral['priority']
                }
                self.jct_portfolio[code]['num'] -= collateral_num

                collateral_total_value = 0
                print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                break

            # to next collateral
            self.collateral_portfolio[code] = {
                'num': collateral['num'],
                'is_usd': collateral['is_usd'],
                'price': collateral['price'],
                'priority': collateral['priority']
            }
            collateral_total_value -= collateral['price'] * collateral['num']
            self.jct_portfolio[code]['num'] = 0

        if collateral_total_value > 0:
            raise ValueError(f'Initial JCT is insufficient!! {self.jct_portfolio}')

        collateral_sum = update_portfolio_price(self.collateral_portfolio, self.start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        self.logs['date'] = [self.start_date]
        self.logs['st_total_value'] = [st_total_value]
        self.logs['jct_total_value'] = [jct_total_value]
        self.logs['jct_portfolio'] = [copy.deepcopy(self.jct_portfolio)]
        self.logs['collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]
        self.logs['collateral_sum'] = [collateral_sum]
        self.logs['necessary_collateral_value'] = [self.necessary_collateral_value]
        self.logs['lender_additional_issue'] = [False]
        self.logs['borrower_additional_issue'] = [False]
        self.logs['has_done_margincall'] = [True]

        self.initial_collateral_portfolio = copy.deepcopy(self.collateral_portfolio)
        self.logs['initial_collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]

        print('Transaction is created.')
        if self.print_log:
            pprint(self.logs)

    def execute(self):
        for _date in self.date_range():
            print("@" * 80)
            print(_date)
            self.check_diff_and_margin_call(_date)
            print("@" * 80)

        print("Finished!!!!")

        return self.logs
