from calendar import c
import copy
from datetime import date
import math
from pprint import pprint
from typing import Dict, List, Optional, TypedDict, Union

from .utils import update_portfolio_price

class JCTVariableTransaction(object):
    """
    JCT可変複数
    トランザクションごとに固有のJCTを発行
    """

    def __init__(self, jct_portfolio: dict, st_portfolio: dict, start_date: Union[str, date], borrower: str = 'Borrower(A)', lender: str = 'Lender(B)',
                 borrower_loan_ratio: float = 1.0, lender_loan_ratio: float = 1.0, print_log: bool = False, auto_deposit: bool=False) -> None:
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
            print('*'*50)
            print('*'*50)
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



PortfolioItem = TypedDict('PortfolioItem', {'num': int, 'price': Optional[int], 'is_usd': bool})
PortfolioWithPriorityItem = TypedDict('PortfolioWithPriorityItem', {'num': int, 'price': Optional[int], 'priority': Optional[int], 'is_usd': bool})

class AutoAdjustmentTransaction(JCTVariableTransaction):
  """
  JCT＝日本円、のような形で扱い、担保としてSTも差し入れられるようにする
  これによって双方がSTをやり取りするような形になる
  **借り手側が差し入れる担保に優先順位をつけ、価格調整にJCT以外のトークンも用いられるようにする
  **これによってJCTの追加差し入れ等をせずに自動で価格調整ができる
  """
  def __init__(self, jct_portfolio: Dict[str, PortfolioWithPriorityItem], st_portfolio: Dict[str, PortfolioItem], start_date: Union[str, date], borrower: str = 'Borrower(A)', lender: str = 'Lender(B)', borrower_loan_ratio: float = 1, lender_loan_ratio: float = 1, print_log: bool = False, auto_deposit: bool = False) -> None:
      self.borrower = borrower
      self.lender = lender
      self.jct_portfolio = copy.deepcopy(jct_portfolio)
      self.st_portfolio = copy.deepcopy(st_portfolio)
      self.borrower_loan_ratio = borrower_loan_ratio
      self.lender_loan_ratio = lender_loan_ratio
      self.print_log = print_log
      self.auto_deposit = auto_deposit
      self.collateral_portfolio: Dict[str, PortfolioWithPriorityItem] = {}
      self.logs = []
      pprint(f'JCT portfolio: {self.jct_portfolio}')
      pprint(f'ST portfolio: {self.st_portfolio}')

      st_total_value = update_portfolio_price(self.st_portfolio, start_date, print_log)
      jct_total_value = update_portfolio_price(self.jct_portfolio, start_date, print_log)
      collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
      self.necessary_collateral_value =  collateral_total_value

      for code, collateral in sorted(self.jct_portfolio.items(), key =lambda x: x[1]['priority'], reverse=True): # type ignore
        pprint(f'{code}: {collateral}')
        collateral_value = collateral['price'] * collateral['num']
        if collateral_value >= collateral_total_value:
          collateral_num = math.ceil(collateral_value / collateral['price']) 
          self.jct_portfolio[code]['num'] -= collateral_num
          self.collateral_portfolio[code] = {
            'num': collateral_num,
            'is_usd': collateral['is_usd'],
            'price': collateral['price'],
            'priority': collateral['priority']
          }
          collateral_total_value = 0
          print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
          break

        # to next collateral
        self.jct_portfolio[code]['num'] = 0
        self.collateral_portfolio[code] = {
          'num': collateral['num'],
          'is_usd': collateral['is_usd'],
          'price': collateral['price'],
          'priority': collateral['priority']
        }
        collateral_total_value -= collateral['price'] * collateral['num']
        

      if collateral_total_value > 0:
          raise ValueError(f'Initial JCT is insufficient!! {self.jct_portfolio}')

      log = {
          'date': start_date,
          'st_total_value': st_total_value,
          'jct_total_value': jct_total_value,
          'collateral_portfolio': self.collateral_portfolio,
          'necessary_collateral_value': self.necessary_collateral_value
      }

      self.logs.append(log)

      print('Transaction is created.')
      if self.print_log:
          pprint(log)

  def check_diff_and_margin_call(self, date: Union[str, date]):
      """
      JCT, STそれぞれの時価更新を行い、差分の算出、価格調整を行う
      差し入れている担保の優先寺度に従って差し入れていくことで、複数の担保がある際の
      価格調整用担保の追加差し入れのような事態を防ぐ
      """
      st_total_value = update_portfolio_price(self.st_portfolio, date, self.print_log)
      jct_total_value = update_portfolio_price(self.jct_portfolio, date, self.print_log)
      update_portfolio_price(self.collateral_portfolio, date)
      # 預け入れるべき担保額
      collateral_total_value = st_total_value * self.lender_loan_ratio / self.borrower_loan_ratio
      self.necessary_collateral_value = collateral_total_value

      for code, collateral in sorted(self.jct_portfolio.items(), key=lambda x: x[1]['priority'], reverse=True): # type ignore
        pprint(f'{code}: {collateral}')
        collateral_value = collateral['price'] * collateral['num']
        if collateral_value >= collateral_total_value:
          collateral_num = math.ceil(collateral_value / collateral['price']) 
          self.jct_portfolio[code]['num'] -= collateral_num

          if code in self.collateral_portfolio:
            self.collateral_portfolio[code]['num'] += collateral_num
          else:
            self.collateral_portfolio[code] = {
              'num': collateral_num,
            'is_usd': collateral['is_usd'],
            'price': collateral['price'],
            'priority': collateral['priority']
            }
          collateral_total_value = 0
          print("@@@@@@@@@@@@@@price adjustment is successfully done@@@@@@@@@@@@@@")
          break

        # to next collateral
        self.jct_portfolio[code]['num'] = 0
        if code in self.collateral_portfolio:
          self.collateral_portfolio[code]['num'] += collateral['num']
        else:
          self.collateral_portfolio[code] = {
            'num': collateral['num'],
            'is_usd': collateral['is_usd'],
            'price': collateral['price'],
            'priority': collateral['priority']
          }

        collateral_total_value -= collateral['price'] * collateral['num']
        
      log = {
          'date': date,
          'st_total_value': st_total_value,
          'jct_total_value': jct_total_value,
          'collateral_portfolio': self.collateral_portfolio,
      }

      self.logs.append(log)
      if self.print_log:
          print('OK. collateral is moved.')
          pprint(log)