class MockPortfolio:
    """
    Simulates a trading account with cash, asset holdings, and risk management.
    """

    def __init__(self, initial_cash: float = 100000.0, stop_loss_pct: float = 0.02):
        self.cash = initial_cash
        self.holdings: dict[str, dict] = {}  # {symbol: {"quantity": int, "avg_price": float}}
        self.history: list[dict] = []  # Records of closed trades
        self.stop_loss_pct = stop_loss_pct  # 2% default stop loss

    def buy(self, symbol: str, price: float, quantity: int = 10):
        total_cost = price * quantity
        if total_cost > self.cash:
            print(f"⚠️ Insufficient funds to buy {symbol}")
            return False

        self.cash -= total_cost

        if symbol not in self.holdings:
            self.holdings[symbol] = {"quantity": 0, "avg_price": 0.0}

        # Calculate new average price
        current = self.holdings[symbol]
        new_total_qty = current["quantity"] + quantity
        current["avg_price"] = ((current["avg_price"] * current["quantity"]) + total_cost) / new_total_qty
        current["quantity"] = new_total_qty

        print(f"✅ BOUGHT {quantity} of {symbol} at {price:.2f}. New Balance: {self.cash:.2f}")
        return True

    def sell(self, symbol: str, price: float, reason: str = "SIGNAL"):
        if symbol not in self.holdings or self.holdings[symbol]["quantity"] == 0:
            return False

        holding = self.holdings[symbol]
        qty = holding["quantity"]
        entry_price = holding["avg_price"]

        revenue = price * qty
        profit_loss = revenue - (entry_price * qty)
        profit_percent = (profit_loss / (entry_price * qty)) * 100

        self.cash += revenue
        self.holdings[symbol] = {"quantity": 0, "avg_price": 0.0}  # Reset holdings

        print(f"--- 💰 TRADE CLOSED ({reason}): {symbol} ---")
        print(f"Action: SELL at {price:.2f} (Entry: {entry_price:.2f})")
        print(f"PnL: ${profit_loss:.2f} ({profit_percent:.2f}%)")
        print(f"Current Cash: ${self.cash:.2f}")
        print(f"-------------------------------")
        return True

    def check_risk_management(self, symbol: str, current_price: float):
        """
        Checks if the current market price triggers a stop loss for a holding.

        """
        if symbol in self.holdings and self.holdings[symbol]["quantity"] > 0:
            entry_price = self.holdings[symbol]["avg_price"]
            price_change = (current_price - entry_price) / entry_price

            if price_change <= -self.stop_loss_pct:
                print(f"🚨 STOP LOSS TRIGGERED for {symbol} at {current_price:.2f}")
                self.sell(symbol, current_price, reason="STOP LOSS")