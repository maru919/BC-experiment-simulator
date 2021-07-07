from .simulator import Transaction

jct_portfolio = []
st_portfolio = []
start_datetime_str = '2021-05-25 10:00:00'
end_datetime_str = '2021-06-01 10:00:00'
loan_ratio = 1.05

# margin_call_threshold = 0.2

# トランザクションを初期化
transaction = Transaction(jct_portfolio, st_portfolio, start_datetime_str, end_datetime_str, loan_ratio)

# 毎日15時に時価を更新し、差分を確認する
transaction.update_price_all()
value_diff = transaction.check_value_diff()
# マージンコールを自動で行う場合、初めに設定した値に応じてマージンコールを発生させる
if マージンコールが発生する場合:
    transaction.margin_call()

transaction.settle()
