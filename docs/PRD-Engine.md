# Product Requirements Document: AlgoTrade Engine

## Product Name & Description

**AlgoTrade Engine** — A trading algorithm execution engine that consumes real-time market ticks from Redis, runs multiple strategies per symbol, aggregates signals via majority voting, and executes trades through a mock portfolio with configurable risk management.

---

## Goals & Non-Goals

### Goals

- **Reliable execution**: Consume normalized ticks from Redis (published by the Ingestor), run registered strategies per symbol, and execute trades when a clear majority signal is reached.
- **Multi-strategy support**: Run several technical and statistical strategies per symbol (e.g., SMA crossover, Bollinger Bands, VWAP, MACD, RSI, Z-Score, Price Alert) with configurable parameters.
- **Deterministic signal aggregation**: Use majority voting (>50% non-HOLD) to reduce noise and avoid conflicting single-strategy signals.
- **Controlled risk**: Maintain an in-memory mock portfolio with configurable stop-loss (e.g., 2%) and consistent execution rules (fixed buy size, full-position sell).
- **Operational visibility**: Expose a health endpoint for monitoring and support per-symbol strategy configuration for different assets.

### Non-Goals

- Replacing or competing with the Ingestor; the Engine is a consumer of normalized data only.
- Live brokerage integration; execution is limited to the mock portfolio for simulation.
- Providing a UI or dashboard; the Engine is a headless service.
- Guaranteeing profitability or suitability for live capital; the system is for research and simulation.

---

## User Personas

| Persona | Role | Primary Need |
|--------|------|--------------|
| **Quant / Researcher** | Develops and backtests strategies | Run multiple strategies per symbol with tunable parameters and see aggregated signals and execution behavior. |
| **Algorithmic Trader** | Operates or evaluates automated strategies | Understand how signals are combined (majority vote) and how risk (stop-loss) is applied in a simulated environment. |
| **Developer** | Integrates or extends the system | Clear APIs, Redis contract, and pluggable strategy interface to add new strategies or adapt execution logic. |

---

## Core Features

### 1. Signal Engine

- Subscribes to Redis channels **per symbol** (channel name = symbol).
- Receives **NormalizedTick** messages (symbol, price, quantity, timestamp, received_at).
- For each tick: updates market price for risk checks, saves price to Redis history for strategies, runs all registered strategies for that symbol, collects BUY/SELL/HOLD votes.
- Applies **majority rule**: if >50% of non-HOLD votes agree on BUY or SELL, triggers execution; otherwise no trade.

### 2. Strategies

- Each strategy implements a common interface and returns **ActionEnum** (BUY, SELL, HOLD).
- **Included strategies**: PriceAlertStrategy, SMACrossoverStrategy, BollingerBandsStrategy, VWAPStrategy, MACDStrategy, ZScoreStrategy, RSI.
- Strategies can use **RedisHandler** to read price history (e.g. `history:{symbol}`) for warm-up and indicators.
- Per-symbol configuration in application setup (e.g., threshold, fast/slow periods) allows different parameters per asset.

### 3. Execution Engine

- Executes **BUY**: fixed quantity (e.g., 10 units) via MockPortfolio.
- Executes **SELL**: full position for the symbol.
- Updates current market price for the portfolio so **stop-loss** can be evaluated on every tick.

### 4. Mock Portfolio

- **In-memory** state: cash, holdings (symbol → quantity, average price), and trade history.
- **Buy**: deducts cash, updates or creates position and average price.
- **Sell**: closes full position, records PnL, adds cash.
- **Risk**: Configurable stop-loss (e.g., 2%); when current price falls below threshold from average entry, position is closed automatically.

### 5. Redis Integration

- **Subscriber**: Listens to symbol-named channels for incoming ticks.
- **RedisHandler**: Writes latest price into history for strategies; reads history for strategy warm-up and indicator calculation.

---

## Data Flow

```
Ingestor → Redis (PUBLISH per symbol, LPUSH+LTRIM history:{symbol})
                ↓
         Engine subscribes to symbol channels
                ↓
         SignalEngine receives NormalizedTick
                ↓
         Update market price (risk) + save price to history
                ↓
         Run all strategies for symbol → collect votes
                ↓
         Majority vote → if BUY/SELL majority → ExecutionEngine
                ↓
         MockPortfolio: buy (fixed units) or sell (full position)
                ↓
         Stop-loss checked on each tick via updated market price
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.12+ |
| API / Server | FastAPI |
| Messaging / Cache | Redis (pub/sub + key-value for history) |
| Validation / DTOs | Pydantic |
| Deployment | Service runs on **port 8001** |

---

## Configuration

- **Per-symbol strategy config** (e.g., in main): threshold for price alert, fast/slow periods for SMA/MACD, period for Z-Score, etc.
- **Health**: `GET /health` returns service status (e.g., healthy, provider name).

---

## Out of Scope / Future Considerations

- **Live brokerage**: No real order routing; mock portfolio only.
- **Persistence**: Portfolio and history are in-memory; restart loses state unless explicitly persisted later.
- **Multi-instance coordination**: Single Engine instance per deployment; no distributed locking or leader election.
- **Strategy backtesting**: Engine is real-time only; backtesting would be a separate service or mode.
- **Dynamic strategy registration**: Strategies are registered at startup; adding/removing at runtime is not in scope.
- **Crypto vs. stocks**: Same pipeline; symbol filtering (e.g., for Alpaca StockDataStream) is handled by the Ingestor; Engine treats all symbols uniformly once ticks arrive.

---

## Summary

The Engine is the **execution brain** of the AlgoTrade stack: it turns real-time normalized ticks into strategy votes, aggregates them by majority, and runs a simulated book with fixed execution rules and stop-loss risk management. It is designed for clarity, testability, and extensibility (new strategies, configurable parameters) while staying strictly within a mock execution environment.
