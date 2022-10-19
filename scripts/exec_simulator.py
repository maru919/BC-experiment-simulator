import copy
from datetime import date, timedelta
import math
from pprint import pprint
from typing import Dict

from .utils import update_portfolio_price

from .types import PortfolioItem, PortfolioWithPriorityItem
from .variableLocal import  AutoAdjustmentTransaction

class ExecuteAutoAdjustmentTransaction(AutoAdjustmentTransaction):
    def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: date, end_date: date, borrower: str = 'Borrower(A)', lender: str = 'Lender(B)', borrower_loan_ratio: float = 1, lender_loan_ratio: float = 1, print_log: bool = False, auto_deposit: bool = False) -> None:
        self.borrower = borrower
        self.lender = lender
        self.jct_portfolio = copy.deepcopy(jct_portfolio)
        self.st_portfolio = copy.deepcopy(st_portfolio)
        self.borrower_loan_ratio = borrower_loan_ratio
        self.lender_loan_ratio = lender_loan_ratio
        self.print_log = print_log
        self.auto_deposit = auto_deposit
        self.collateral_portfolio: Dict[str, PortfolioWithPriorityItem] = {}
        self.logs: Dict[str, list] = {}
        self.start_date = start_date
        self.print_log = print_log

        pprint(f'JCT portfolio: {self.jct_portfolio}')
        pprint(f'ST portfolio: {self.st_portfolio}')

        def date_range():
            for n in range(int((end_date - start_date).days) -1):
                yield start_date + timedelta(n+1)
        
        # 初日は初期化処理を含むため、2日目以降のgeneratorを作成
        self.date_range = date_range

        self.initialize()
    
    def initialize(self):
        st_total_value = update_portfolio_price(self.st_portfolio, self.start_date, self.print_log)
        jct_total_value = update_portfolio_price(self.jct_portfolio, self.start_date, self.print_log)
        collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
        self.necessary_collateral_value =  collateral_total_value
        
        for code, collateral in sorted(self.jct_portfolio.items(), key =lambda x: x[1]['priority'], reverse=True): # type: ignore
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

        log = {
            'date': self.start_date,
            'st_total_value': st_total_value,
            'jct_total_value': jct_total_value,
            'jct_portfolio': copy.deepcopy(self.jct_portfolio),
            'collateral_portfolio': copy.deepcopy(self.collateral_portfolio),
            'necessary_collateral_value': self.necessary_collateral_value
        }
        self.logs['date'] = [self.start_date]
        self.logs['st_total_value'] = [st_total_value]
        self.logs['jct_total_value'] = [jct_total_value]
        self.logs['jct_portfolio'] = [copy.deepcopy(self.jct_portfolio)]
        self.logs['collateral_portfolio'] = [copy.deepcopy(self.collateral_portfolio)]
        self.logs['necessary_collateral_value'] = [self.necessary_collateral_value]

        print('Transaction is created.')
        if self.print_log:
            pprint(self.logs)
    
    def execute(self):
        for date in self.date_range():
            print("@"*80)
            print(date)
            self.check_diff_and_margin_call(date)
            print("@"*80)

        print("Finished!!!!")

        return self.logs

