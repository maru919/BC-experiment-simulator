from typing import Optional, TypedDict

PortfolioItem = TypedDict('PortfolioItem', {
    'num': int,
    'price': int,
    'is_usd': bool
})
PortfolioWithPriorityItem = TypedDict('PortfolioWithPriorityItem', {
    'num': int,
    'price': int,
    'priority': Optional[int],
    'is_usd': bool
})

TransactionOption = TypedDict('TransactionOption', {
    'borrower': Optional[str],
    'lender': Optional[str],
    'borrower_loan_ratio': Optional[float],
    'lender_loan_ratio': Optional[float],
    'print_log': Optional[bool],
    'auto_deposit': Optional[bool],
    'is_dummy_data': Optional[bool],
    'is_reverse': Optional[bool],
    'margin_call_threshold': Optional[float],
    'is_manual': Optional[bool],
})
