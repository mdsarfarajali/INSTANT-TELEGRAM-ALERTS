import logging
import asyncio
import yfinance as yf

logger = logging.getLogger(__name__)

class NiftyPriceStream:
    """
    Real-time NIFTY 50 Price Stream using Yahoo Finance (^NSEI).
    This provides free, near real-time polling data without requiring daily tokens.
    """
    def __init__(self, on_tick_callback, symbol: str = "^NSEI", interval: float = 3.0):
        self.on_tick_callback = on_tick_callback
        self.symbol = symbol
        self.interval = interval
        self.running = False
        self._task = None

    async def start(self):
        self.running = True
        logger.info(f"🚀 NIFTY Price Stream started (Polling {self.symbol} every {self.interval}s)")
        
        while self.running:
            try:
                # Polling Yahoo Finance for the latest Nifty price
                ticker = yf.Ticker(self.symbol)
                
                # Fetching 1m history to get the absolute latest tick reliably
                data = ticker.history(period="1d", interval="1m")
                if not data.empty:
                    ltp = float(data['Close'].iloc[-1])
                    await self.on_tick_callback(ltp)
                else:
                    logger.warning(f"No price data returned for {self.symbol}")
                
            except Exception as e:
                logger.error(f"Error polling NIFTY price: {e}")
            
            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False
        logger.info("Stopping NIFTY Price Stream...")
