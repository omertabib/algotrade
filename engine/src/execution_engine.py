from src.enums import ActionEnum
from src.mock_portfolio import MockPortfolio


class ExecutionEngine:
    """
    Executes trades and monitors risk against the MockPortfolio based on signals.
    """

    def __init__(self, portfolio: MockPortfolio):
        self.portfolio = portfolio

    async def execute_trade(self, symbol: str, action: ActionEnum, price: float):
        if action == ActionEnum.BUY:
            # For this simulation, we buy 10 units per signal
            self.portfolio.buy(symbol, price, quantity=10)

        elif action == ActionEnum.SELL:
            # Sell the entire position for this symbol
            self.portfolio.sell(symbol, price, reason="MAJORITY SIGNAL")

    async def update_market_price(self, symbol: str, price: float):
        """
        Updates the current price to check for automated risk triggers like stop-loss.

        """
        self.portfolio.check_risk_management(symbol, price)