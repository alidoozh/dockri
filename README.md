# AlidoozhEngine_Pro

BTC-only smart trading engine:

- Indicators: RSI, MACD, Volume (z), Whale activity (proxy), Market state (EMA spread), ATR, Regime filter, Sentiment placeholder
- Models: MLP/LSTM (scikit-learn), DRL (SAC via SB3)
- Decision engine: Bayesian-like update + Hedge-style weighting
- Feedback loop from TP/SL outcomes (auto weight update)
- Free price API: CoinGecko (default) with Binance fallback
- Telegram alerts with Entry/SL/TP/RR/Confidence
- UI (FastAPI + Jinja2) and JSON APIs
- Poll every 2 seconds (configurable by `POLL_INTERVAL`)

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Open http://localhost:8000

On startup it sends a Telegram test message.
