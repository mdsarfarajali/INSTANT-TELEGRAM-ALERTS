import logging
import asyncio
import json
import websockets

logger = logging.getLogger(__name__)

class XAUUSDPriceStream:
    """
    Real-time Gold Price Stream using Binance Public WebSocket (PAXG/USDT).
    PAXG is a gold-pegged token that tracks XAUUSD spot price accurately.
    """
    def __init__(self, on_tick_callback, symbol: str = "paxgusdt"):
        self.on_tick_callback = on_tick_callback
        self.symbol = symbol.lower()
        self.uri = f"wss://stream.binance.com:9443/ws/{self.symbol}@ticker"
        self.running = False
        self._task = None

    async def start(self):
        self.running = True
        logger.info(f"🚀 Binance WebSocket started (Tracking {self.symbol.upper()} for Gold Spot)")
        
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logger.info(f"✅ Connected to Binance Stream for {self.symbol.upper()}")
                    while self.running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # 'c' is the field for current price (Close) in Binance ticker
                        if 'c' in data:
                            ltp = float(data['c'])
                            await self.on_tick_callback(ltp)
                            
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Binance WebSocket Error: {e}. Reconnecting in 5s...")
                    await asyncio.sleep(5)
                else:
                    break

    def stop(self):
        self.running = False
        logger.info("Stopping Binance WebSocket stream...")
