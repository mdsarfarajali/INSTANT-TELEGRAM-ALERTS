import logging
from xauusd.storage.database import get_active_levels, deactivate_level, log_trigger
import xauusd.storage.portfolio as portfolio
from xauusd.core.trade_logic import calculate_trade_params

logger = logging.getLogger(__name__)


class TriggerChecker:
    def __init__(self, alert_callback):
        self.alert_callback = alert_callback
        self.prev_price = None
        self.triggered_ids = set() # Safety lock

    async def check_ticks(self, current_price: float):
        if self.prev_price is None:
            self.prev_price = current_price
            return

        active_levels = await get_active_levels()

        for level in active_levels:
            level_id = level["id"]
            if level_id in self.triggered_ids:
                continue
                
            target_level = float(level["price"])

            # Touch logic: Pure wick/LTP touch
            touched = (
                (self.prev_price < target_level <= current_price) or  # price moved up through level
                (self.prev_price > target_level >= current_price) or  # price moved down through level
                (current_price == target_level)                        # exact match
            )

            if touched:
                self.triggered_ids.add(level_id) # Lock immediately
                await self.trigger_signal(level, current_price)

        # --- Paper Trading Monitoring ---
        open_trades = await portfolio.get_open_trades()
        for trade in open_trades:
            trade_id = trade["id"]
            ttype = trade["trade_type"]
            tp = trade["target_price"]
            sl = trade["sl_price"]
            
            closed_status = None
            pnl = 0.0
            
            if ttype == "CALL":
                if current_price >= tp:
                    closed_status, pnl = "PROFIT", 5.0
                elif current_price <= sl:
                    closed_status, pnl = "LOSS", -5.0
            elif ttype == "PUT":
                if current_price <= tp:
                    closed_status, pnl = "PROFIT", 5.0
                elif current_price >= sl:
                    closed_status, pnl = "LOSS", -5.0
            else: # TOUCH fallback (if used)
                if current_price >= tp or current_price <= sl:
                    closed_status, pnl = "PROFIT", 5.0 # Just score it
                    
            if closed_status:
                await portfolio.close_trade(trade_id, closed_status, pnl)
                # Send exit alert
                exit_data = {
                    "instrument": "GOLD",
                    "type": ttype,
                    "exit_status": closed_status,
                    "pnl": pnl,
                    "exit_price": current_price
                }
                await self.alert_callback(exit_data)

        self.prev_price = current_price

    async def trigger_signal(self, level: dict, current_price: float):
        level_id = level["id"]
        level_type = level["level_type"]
        level_price = float(level["price"])

        await deactivate_level(level_id)
        trade = calculate_trade_params(level_price, level_type)

        await log_trigger(
            level_id=level_id,
            price=current_price,
            level_type=level_type,
            entry=trade["entry"],
            target=trade["target"],
            sl=trade["sl"]
        )

        # 3b. Open Virtual Trade in Portfolio
        await portfolio.open_virtual_trade(
            level_id=level_id,
            trade_type=level_type,
            entry_price=trade["entry"],
            target_price=trade["target"],
            sl_price=trade["sl"]
        )

        # Fire Telegram alert
        await self.alert_callback(trade)

        logger.info(f"✅ XAUUSD Signal Triggered: {level_type} at {level_price} | LTP: {current_price}")
