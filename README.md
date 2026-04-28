# Trading Bot

A modular, extensible trading bot framework built in Python. The architecture follows a strict pipeline: Strategy → Signal → RiskManager → Order → Broker → Execution.

## Architecture

- **Strategies**: Generate trading signals based on market data (RSI, MA Crossover, MA Trend, Open/Close Rank)
- **Risk Manager**: Applies position sizing and safety checks
- **Broker**: Handles API communication with Trading212
- **Engine**: Orchestrates the data flow and execution loop
- **Data Feed**: Fetches market data via yfinance
- **Portfolio**: Tracks current positions
- **Metrics**: Records executed trades

## Deployment

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your API credentials in `secrets/secrets.json`:
   ```json
   {
     "api_key": "your_api_key",
     "secret": "your_secret"
   }
   ```

3. Review and modify `config.json` for your trading preferences:
   - Set `live: true` only when ready for real trading (defaults to demo mode)
   - Activate/deactivate strategies via the `active` flag
   - Adjust symbols and data feed parameters

4. Run the bot:
   ```bash
   python main.py
   ```

   To run a specific strategy regardless of config:
   ```bash
   python main.py --strategy MACrossoverStrategy
   ```

## Adding a New Strategy

1. Create a new file in `strategies/` (e.g., `strategies/my_strategy.py`)

2. Implement the Strategy interface:
   ```python
   from typing import Any, List, Optional
   from core.models import Signal, SignalType
   from core.strategy import Strategy

   class MyStrategy(Strategy):
       def __init__(self, symbols: Optional[List[str]] = None):
           self._symbols = symbols

       @property
       def name(self) -> str:
           return "MyStrategy"

       def on_data(self, data: Any) -> List[Signal]:
           signals = []
           # Your strategy logic here
           return signals
   ```

3. Export it from `strategies/__init__.py`:
   ```python
   from .my_strategy import MyStrategy
   __all__ = ["MyStrategy", ...]
   ```

4. Register in `core/strategy_factory.py`:
   ```python
   from strategies import MyStrategy
   
   if name == "MyStrategy":
       strategies.append(MyStrategy(symbols=symbols))
   ```

5. Add to `config.json`:
   ```json
   {"name": "MyStrategy", "symbols": ["AAPL", "MSFT"], "active": true}
   ```

## Strategy-Specific Configuration Notes

### RSIStrategy
- Uses 14-period RSI calculation
- Default data_feed.period: "3mo" is sufficient
- BUY when RSI < 30, SELL when RSI > 70

### MACrossoverStrategy
- Uses 10-period and 50-period moving averages
- Default data_feed.period: "3mo" is sufficient
- BUY when fast MA crosses above slow MA, SELL when fast crosses below

### MATrendStrategy
- Uses 50-period and 200-period moving averages
- **Important**: For 200-period MA calculation, change data_feed.period from "3mo" to "1y" and keep interval as "1d"
- BUY when 50 MA crosses above 200 MA, SELL when 50 crosses below

### OpenCloseRankStrategy
- Rank-based strategy using open/close price ratios
- Default data_feed.period: "3mo" is sufficient
- Performs sub-industry neutralization and winsorization
