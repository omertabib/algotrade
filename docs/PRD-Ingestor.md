# Product Requirements Document: AlgoTrade Ingestor

## Product Name & Description

**AlgoTrade Ingestor** — A real-time market data ingestion service that fetches live ticks from providers (e.g., Alpaca), normalizes them into a common schema, and publishes them to Redis for the Engine to consume, while maintaining a short price history in Redis for strategy warm-up.

---

## Goals & Non-Goals

### Goals

- **Real-time ingestion**: Connect to provider live streams (e.g., Alpaca StockDataStream), subscribe to configured symbols, and process each trade event with low latency.
- **Provider-agnostic contract**: Normalize provider-specific payloads into a single **NormalizedTick** schema (symbol, price, quantity, timestamp, received_at) so downstream consumers are independent of the data source.
- **Reliable distribution**: Publish every valid tick to Redis on a **per-symbol channel** so the Engine can subscribe by symbol.
- **Strategy support**: Maintain a bounded price history in Redis (e.g., last 100 points per symbol) via list operations for Engine strategy warm-up and indicators.
- **Operational visibility**: Health endpoint reporting service status, Redis connectivity, and tracked symbols.

### Non-Goals

- Trading or signal generation; the Ingestor only fetches and distributes data.
- Historical backfill or replay; focus is live streaming only.
- Guaranteeing tick completeness or exactly-once delivery; best-effort real-time distribution.
- Storing long-term history; only a short rolling window is kept in Redis.

---

## User Personas

| Persona | Role | Primary Need |
|--------|------|--------------|
| **Quant / Researcher** | Needs live data for strategies | Reliable stream of normalized ticks for chosen symbols, with minimal configuration. |
| **Algorithmic Trader** | Operates automated systems | Single pipeline for multiple symbols, with clear health and connectivity status. |
| **Developer** | Integrates or extends the system | Extensible provider abstraction (base class + Alpaca implementation), clear Redis channel and key layout, and a consistent NormalizedTick schema. |

---

## Core Features

### 1. Data Fetching

- Connects to provider **live stream** (e.g., Alpaca `StockDataStream`).
- Subscribes to **configurable symbols** (e.g., AAPL, TSLA, GOOG, BTC/USD).
- **Symbol filtering**: For providers that separate stock vs. crypto (e.g., StockDataStream), symbols containing "/" (e.g., BTC/USD) are filtered out of the stock stream to avoid provider errors; crypto can be added via a separate stream or provider when supported.
- On each trade event, the raw payload is validated and transformed to **NormalizedTick**.

### 2. Provider Abstraction

- **DataProvider** base class defines the interface for transforming provider-specific DTOs into the common format.
- **AlpacaDataProvider**: Maps Alpaca trade payload (e.g., AlpacaTick DTO with symbol, price, size, time) to NormalizedTick; validates price > 0 and returns a Result type for errors (e.g., invalid price).
- New providers (e.g., other brokers or data vendors) can be added by implementing the same transform contract.

### 3. Normalization

- **NormalizedTick** schema: symbol, price, quantity, timestamp (event time), received_at (ingestion time).
- Ensures downstream Engine and strategies see a single, consistent structure regardless of provider.
- Invalid or rejected events (e.g., price ≤ 0) are not published; errors can be logged or surfaced via Result.

### 4. Redis Publish & Cache

- **RedisIngestHandler**:
  - **Publish**: For each NormalizedTick, `PUBLISH` to channel = **symbol** (so subscribers subscribe per symbol).
  - **Cache**: `LPUSH` + `LTRIM` on `history:{symbol}` to keep the last **N** prices (e.g., 100) for strategy warm-up.
- Operations are performed in an **atomic pipeline** to reduce round-trips and keep publish + cache consistent.

### 5. Configuration & Health

- **Configuration**: Provider credentials (e.g., ALPACA_API_KEY, ALPACA_SECRET_KEY) and symbol list (e.g., SYMBOLS_TO_TRACK) via environment or app config.
- **Health endpoint**: Returns service status, **redis_status** (connected/disconnected), **tracked_symbols**, and **provider** name (e.g., Alpaca).

---

## Data Flow

```
Provider (e.g., Alpaca StockDataStream)
         ↓ trade event
DataIngestor._on_trade
         ↓ AlpacaTick DTO
AlpacaDataProvider.transform_data → NormalizedTick (or error)
         ↓
RedisIngestHandler.publish_and_cache
         ↓ atomic pipeline
    PUBLISH channel=symbol, payload=NormalizedTick JSON
    LPUSH + LTRIM history:{symbol} (max 100)
         ↓
Redis (consumed by Engine subscribers + strategy history reads)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.12+ |
| API / Server | FastAPI |
| Market Data | Alpaca SDK (e.g., StockDataStream) |
| Messaging / Cache | Redis (pub/sub + list for history) |
| Validation / DTOs | Pydantic |
| Deployment | Service runs on **port 8000** |

---

## Configuration

- **Environment**: ALPACA_API_KEY, ALPACA_SECRET_KEY, SYMBOLS_TO_TRACK (e.g., AAPL, TSLA, GOOG, BTC/USD).
- **Health**: `GET /health` returns status, redis_status, tracked_symbols, and provider.

---

## Out of Scope / Future Considerations

- **Historical backfill**: No replay or historical load from provider APIs; only live stream.
- **Crypto on Alpaca**: If Alpaca is used, crypto symbols may require a different stream (e.g., CryptoDataStream); current design filters "/" for StockDataStream to avoid 400s.
- **Multi-provider aggregation**: Single active provider per instance; combining multiple providers would require additional routing or aggregation logic.
- **Persistence of raw ticks**: Only normalized ticks are published and cached; no long-term storage in this service.
- **Schema versioning**: NormalizedTick is assumed stable; versioning or compatibility layers could be added later if the schema evolves.

---

## Summary

The Ingestor is the **data pipeline** of the AlgoTrade stack: it connects to a live market data provider, normalizes ticks into a single schema, publishes them to Redis by symbol for the Engine, and maintains a short price history for strategy warm-up. It is designed for clarity, extensibility (new providers via base class), and operational visibility (health and Redis status).
