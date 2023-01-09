import copy
from datetime import date
import math
from pprint import pprint
from typing import Dict, Union

from scripts.types import PortfolioItem, PortfolioWithPriorityItem, TransactionOption

from .utils import update_portfolio_price


class JCTVariableTransaction(object):
    """
    JCT可変複数
    トランザクションごとに固有のJCTを発行
    """

    def __init__(self, jct_portfolio: dict, st_portfolio: dict, start_date: Union[str, date], options: TransactionOption) -> None:
        self.borrower = options['borrower'] if 'borrower' in options else "Borrower(A)"
        self.lender = options['lender'] if 'lender' in options else 'Lender(B)'
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = options['borrower_loan_ratio'] if 'borrower_loan_ratio' in options else 1.0
        self.lender_loan_ratio = options['lender_loan_ratio'] if 'lender_loan_ratio' in options else 1.0
        self.print_log = options['print_log'] if 'print_log' in options else False
        self.auto_deposit = options['auto_deposit'] if 'auto_deposit' in options else True
        self.logs = []
        print(f'JCT portfolio: {self.jct_portfolio}')
        print(f'ST portfolio: {self.st_portfolio}')

        st_total_value = update_portfolio_price(self.st_portfolio, start_date, self.print_log)
        self.lender_jct_num = math.ceil(st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio)
        self.total_jct_num = math.floor(update_portfolio_price(self.jct_portfolio, start_date, self.print_log))
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
        if self.print_log:
            pprint(log)

    def check_diff_and_margin_call(self, date: Union[str, date]):
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


class AutoAdjustmentTransactionBase(object):
    """
    JCT＝日本円、のような形で扱い、担保としてSTも差し入れられるようにする
    これによって双方がSTをやり取りするような形になる
    **optionで借り手側が差し入れる担保に優先順位をつけ、価格調整にJCT以外のトークンも用いられるようにする
    **これによってJCTの追加差し入れ等をせずに自動で価格調整ができる
    """

    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: Union[str, date], options: TransactionOption) -> None:
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

        pprint(f'JCT portfolio: {self.jct_portfolio}')
        pprint(f'ST portfolio: {self.st_portfolio}')

        st_total_value = update_portfolio_price(self.st_portfolio, start_date, self.print_log, is_dummy_data=self.is_dummy_data)
        jct_total_value = update_portfolio_price(self.jct_portfolio, start_date, self.print_log, is_dummy_data=self.is_dummy_data)
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

        self.logs['date'] = [start_date]
        self.logs['st_total_value'] = [st_total_value]
        self.logs['jct_total_value'] = [jct_total_value]
        self.logs['jct_portfolio'] = [copy.deepcopy(self.jct_portfolio)]
        self.logs['collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]
        self.logs['necessary_collateral_value'] = [self.necessary_collateral_value]
        self.logs['additional_issue'] = [False]

        # 初日のcollateral_portfolioを比較用に保管しておく
        self.initial_collateral_portfolio = copy.deepcopy(self.collateral_portfolio)
        self.logs['initial_collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]

        print('Transaction is created.')
        if self.print_log:
            pprint(self.logs)


class AutoAdjustmentTransactionSingle(AutoAdjustmentTransactionBase):
    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: Union[str, date], options: TransactionOption) -> None:
        super().__init__(jct_portfolio, st_portfolio, start_date, options)

    def check_diff_and_margin_call(self, date: Union[str, date]) -> None:
        """
        JCT, STそれぞれの時価更新を行い、差分の算出、価格調整を行う
        差し入れている担保の優先寺度に従って差し入れていくことで、複数の担保がある際の
        価格調整用担保の追加差し入れのような事態を防ぐ
        """
        st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log, is_dummy_data=self.is_dummy_data)
        jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log, is_dummy_data=self.is_dummy_data)
        collateral_sum = update_portfolio_price(self.collateral_portfolio, date, is_dummy_data=self.is_dummy_data)

        # 預け入れるべき担保額
        collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
        self.necessary_collateral_value = collateral_total_value

        # 差し入れるべき担保と現状差し入れている担保価値との価値の差分
        collateral_diff = collateral_total_value - collateral_sum

        if abs(collateral_diff) < collateral_total_value * self.margin_call_threshold:
            print("price diff is so little that auto margin call is cancelled.")
        else:
            # １種のトークンのみで価格調整を行う
            print("adjust with a single token")
            code, collateral = sorted(self.jct_portfolio.items(), key=lambda x: x[1]['priority'], reverse=True)[0]
            if (collateral_diff > 0):
                print(f'from {self.borrower} to {self.lender}')
                # collateral_value = collateral['price'] * collateral['num']
                collateral_num = math.ceil(collateral_diff / collateral['price'])
                if collateral_num <= self.jct_portfolio[code]['num']:
                    self.collateral_portfolio[code]['num'] += collateral_num
                    self.jct_portfolio[code]['num'] -= collateral_num
                    print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                    self.logs['additional_issue'].append(False)
                else:
                    # 足りない場合はborrowerが追加発行を行う
                    print("collateral num is short@@@@@@@@@")
                    print(f"!!!!additional token issuing by {self.borrower}!!!!")
                    self.collateral_portfolio[code]['num'] += collateral_num
                    self.jct_portfolio[code]['num'] = 0
                    self.logs['additional_issue'].append(True)
            else:
                print(f'from {self.lender} to {self.borrower}')
                collateral_diff = abs(collateral_diff)
                collateral_num = math.ceil(collateral_diff / collateral['price'])
                if collateral_num <= self.collateral_portfolio[code]['num']:
                    self.collateral_portfolio[code]['num'] -= collateral_num
                    self.jct_portfolio[code]['num'] += collateral_num
                    print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                    self.logs['additional_issue'].append(False)
                else:
                    # 足りない場合はlenderが追加発行を行う
                    print("collateral num is slightly short@@@@")
                    print(f"!!!additional token issuing by {self.lender}!!!!")
                    self.collateral_portfolio[code]['num'] = 0
                    self.jct_portfolio[code]['num'] += collateral_num
                    self.logs['additional_issue'].append(True)

        self.logs['date'].append(date)
        self.logs['st_total_value'].append(st_total_value)
        self.logs['jct_total_value'].append(jct_total_value)
        self.logs['jct_portfolio'].append(copy.deepcopy(self.jct_portfolio))
        self.logs['necessary_collateral_value'].append(self.necessary_collateral_value)
        self.logs['collateral_portfolio'].append(copy.deepcopy(self.collateral_portfolio))

        update_portfolio_price(self.initial_collateral_portfolio, date)
        self.logs['initial_collateral_portfolio'].append(copy.deepcopy(self.initial_collateral_portfolio))

        if self.print_log:
            print('OK. collateral is moved.')


class AutoAdjustmentTransactionMulti(AutoAdjustmentTransactionBase):
    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: Union[str, date], options: TransactionOption) -> None:
        super().__init__(jct_portfolio, st_portfolio, start_date, options)

    def check_diff_and_margin_call(self, date: Union[str, date]) -> None:
        """
        JCT, STそれぞれの時価更新を行い、差分の算出、価格調整を行う
        差し入れている担保の優先寺度に従って差し入れていくことで、複数の担保がある際の
        価格調整用担保の追加差し入れのような事態を防ぐ
        """
        st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log, is_dummy_data=self.is_dummy_data)
        jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log, is_dummy_data=self.is_dummy_data)
        collateral_sum = update_portfolio_price(self.collateral_portfolio, date, is_dummy_data=self.is_dummy_data)

        # 預け入れるべき担保額
        collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
        self.necessary_collateral_value = collateral_total_value

        # 差し入れるべき担保と現状差し入れている担保価値との価値の差分
        collateral_diff = collateral_total_value - collateral_sum

        if abs(collateral_diff) < collateral_total_value * self.margin_call_threshold:
            print("price diff is so little that auto margin call is cancelled.")
        else:
            # 複数トークンで価格調整を行う
            if (collateral_diff > 0):
                # borrower -> lender への担保追加差し入れなのでシンプルに優先度が高い順に差し入れ
                print(f'from {self.borrower} to {self.lender}')
                for code, collateral in sorted(self.jct_portfolio.items(), key=lambda x: x[1]['priority'], reverse=True):  # type: ignore
                    pprint(f'{code}: {collateral}')
                    collateral_value = collateral['price'] * collateral['num']
                    if collateral_value >= collateral_diff:
                        collateral_num = math.ceil(collateral_diff / collateral['price'])
                        if (collateral_num > self.jct_portfolio[code]['num']):
                            continue

                        if code in self.collateral_portfolio:
                            self.collateral_portfolio[code]['num'] += collateral_num
                        else:
                            self.collateral_portfolio[code] = {
                                'num': collateral_num,
                                'is_usd': collateral['is_usd'],
                                'price': collateral['price'],
                                'priority': collateral['priority']
                            }

                        self.jct_portfolio[code]['num'] -= collateral_num
                        print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                        self.logs['additional_issue'].append(False)
                        break

                    # to next collateral
                    if code in self.collateral_portfolio:
                        self.collateral_portfolio[code]['num'] += collateral['num']
                    else:
                        self.collateral_portfolio[code] = {
                            'num': collateral['num'],
                            'is_usd': collateral['is_usd'],
                            'price': collateral['price'],
                            'priority': collateral['priority']
                        }
                    collateral_diff -= collateral['price'] * collateral['num']
                    self.jct_portfolio[code]['num'] = 0

            else:
                # lender -> borrower への担保返還なので価格調整用の優先度が低い順に返還(option['is_reverse'])
                collateral_diff = abs(collateral_diff)
                print(f'from {self.lender} to {self.borrower}')
                for code, collateral in sorted(self.collateral_portfolio.items(), key=lambda x: x[1]['priority'], reverse=self.is_reverse):  # type: ignore
                    pprint(f'{code}: {collateral}')
                    collateral_value = collateral['price'] * collateral['num']
                    if collateral_value >= collateral_diff:
                        collateral_num = math.ceil(collateral_diff / collateral['price'])
                        if (collateral_num > self.collateral_portfolio[code]['num']):
                            continue

                        self.jct_portfolio[code]['num'] += collateral_num
                        self.collateral_portfolio[code]['num'] -= collateral_num

                        print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
                        self.logs['additional_issue'].append(False)
                        break

                    # to next collateral
                    self.jct_portfolio[code]['num'] += collateral['num']
                    collateral_diff -= collateral['price'] * collateral['num']
                    self.collateral_portfolio[code]['num'] = 0

        self.logs['date'].append(date)
        self.logs['st_total_value'].append(st_total_value)
        self.logs['jct_total_value'].append(jct_total_value)
        self.logs['jct_portfolio'].append(copy.deepcopy(self.jct_portfolio))
        self.logs['necessary_collateral_value'].append(self.necessary_collateral_value)
        self.logs['collateral_portfolio'].append(copy.deepcopy(self.collateral_portfolio))

        update_portfolio_price(self.initial_collateral_portfolio, date)
        self.logs['initial_collateral_portfolio'].append(copy.deepcopy(self.initial_collateral_portfolio))

        if self.print_log:
            print('OK. collateral is moved.')
