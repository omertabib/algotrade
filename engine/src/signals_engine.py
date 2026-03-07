import asyncio
import os
from collections import Counter
from src.clients.base_subscriber import BaseSubscriber
from src.enums import ActionEnum
from src.execution_engine import ExecutionEngine
from src.handlers.redis_handler import RedisHandler
from src.mappers.redis_signal_mapper import RedisSignalMapper
from src.strategies.base_strategy import BaseStrategy


class SignalEngine:
    def __init__(self, subscriber: BaseSubscriber, cache_handler: RedisHandler, execution: ExecutionEngine):
        self._broker = subscriber
        self._cache = cache_handler
        self.registry: dict[str, list[BaseStrategy]] = dict()
        self._execution = execution

    async def subscribe_to_symbol(self, symbol: str, strategy: BaseStrategy):
        if self.registry.get(symbol) is None:
            self.registry[symbol] = []
        self.registry[symbol].append(strategy)

    async def listen_and_process(self):
        async for message in self._broker.subscribe(list(self.registry.keys())):
            try:
                result = RedisSignalMapper.map(message)
                if not result.is_success:
                    continue

                tick = result.value

                # Update market price first for risk management (Stop Loss)
                await self._execution.update_market_price(tick.symbol, tick.price)

                # Save to cache
                await self._cache.save_price(tick.symbol, tick.price)

                strategies = self.registry.get(tick.symbol, [])
                if not strategies:
                    continue

                # Run all strategies concurrently
                pipeline = [strategy.analyze(tick) for strategy in strategies]
                results = await asyncio.gather(*pipeline)

                # Safe extraction of votes to avoid NoneType errors
                votes = []
                for res in results:
                    if res and res.is_success and res.value:
                        votes.append(res.value.action)

                if not votes:
                    continue

                # Voting logic
                vote_counts = Counter(votes)
                final_action, count = vote_counts.most_common(1)[0]

                if count > len(strategies) / 2 and final_action != ActionEnum.HOLD:
                    print(f"🔥 MAJORITY SIGNAL: {final_action} for {tick.symbol} ({count}/{len(strategies)} votes)")
                    await self._execution.execute_trade(tick.symbol, final_action, tick.price)
                else:
                    if os.getenv("DEBUG", "False").lower() == "true":
                        print(f"DEBUG: {tick.symbol} - Votes: {vote_counts} | No clear majority.")

            except Exception as e:
                print(f"Engine Error: {e}")