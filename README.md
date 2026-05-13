# Multi-Instrument Signal Bot 📈🟡

A professional-grade, high-speed automated Telegram trading bot built with Python.  
This system monitors real-time market prices across multiple instruments and instantly sends Telegram alerts when predefined price levels are touched.

Designed for speed, reliability, and modularity, the bot supports independent tracking systems for both **NIFTY 50** and **Gold (XAUUSD)** with isolated databases and dedicated monitoring engines.

---

# ✨ Features

## 📡 Real-Time Market Tracking

### NIFTY 50
- Live NSE index tracking using Yahoo Finance (`^NSEI`)
- Optimized polling engine for low-latency updates

### 📱 Telegram Commands
- `/start` - View the help menu and formatting rules.
- `/nifty <prices>` - Set Nifty levels (e.g., `/nifty 24800 24700 0 24500`).
- `/xauusd <price>` - Set Gold level (e.g., `/xauusd 2350.50`).
- `/niftyactive` / `/xauusdactive` - View active untriggered levels.
- `/price` - Get the current live Market Price for both instruments.
- `/niftyreset` / `/xauusdreset` - Clear today's levels manually.
- `/opentrades` - View currently running virtual paper trades.
- `/portfolio` - Generate and view your P&L performance graph.

### XAUUSD (Gold)
- True tick-by-tick live spot tracking
- Binance Public WebSocket integration (`PAXGUSDT`)
- Ultra-fast real-time event detection

---

## ⚡ First-Touch Alert Engine
The bot triggers alerts immediately when price touches or wicks into a target level.

✔ No candle-close waiting  
✔ Instant signal delivery  
✔ Millisecond-level reaction speed

---

## 📊 Internal Paper Trading Simulator
The bot acts as a self-contained paper trading exchange!
- **Auto-Execution**: The moment a level is hit, the bot opens a virtual trade in a separate `portfolio.db`.
- **Target & SL**: Automatically calculates +50 points Target and -50 points Stop Loss.
- **Visual P&L Chart**: Generates a cumulative performance line graph tracking all closed trades (+50/-50 per trade).

---

## 🧠 Smart Signal Input
Quickly add multiple levels directly from Telegram.

Example:
```bash
/nifty 24800 24700 0 24500