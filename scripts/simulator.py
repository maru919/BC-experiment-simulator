from .price_data.get_price import GetPriceData

price_getter = GetPriceData()

class Transaction(object):
    def __init__(self, borrower, lender, st_portfolio, init_jct_price, start_datetime_str, weight, margin_call_ratio=0.8):
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
        self.st_portfolio = st_portfolio
        self.start_datetime = start_datetime_str
        self.weight = weight
        self.margin_call_ratio = margin_call_ratio
        self.st_total_value = 0

        self.update_st_price(start_datetime_str)
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

    # def settle(self):
    #     """
    #     決済処理を行う
    #     """
    #     pass

class StableTransaction(Transaction):
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
        self.st_portfolio = st_portfolio
        self.start_datetime = start_datetime
        self.weight = weight
        self.margin_call_ratio = margin_call_ratio
        self.st_total_value = 0

        self.update_st_price(start_datetime)
        self.transaction_jct_num = self.st_total_value * self.weight
        print(f'Initial jct num is {self.transaction_jct_num}.')

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


class JCT(object):
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
