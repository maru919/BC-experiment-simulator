from typing import Optional, TypedDict

PortfolioItem = TypedDict('PortfolioItem', {'num': int, 'price': int, 'is_usd': bool})
PortfolioWithPriorityItem = TypedDict('PortfolioWithPriorityItem', {'num': int, 'price': int, 'priority': Optional[int], 'is_usd': bool})