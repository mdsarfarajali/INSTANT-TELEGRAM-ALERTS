import asyncio
import logging
import threading
import sys

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config.settings import settings
import nifty.storage.database as nifty_db
import nifty.storage.portfolio as nifty_portfolio
import xauusd.storage.database as xauusd_db
import xauusd.storage.portfolio as xauusd_portfolio
from nifty.market.price_stream import NiftyPriceStream
from nifty.core.trigger_checker import TriggerChecker as NiftyTriggerChecker
from nifty.core.reset_manager import setup_scheduler as setup_nifty_scheduler

from xauusd.market.price_stream import XAUUSDPriceStream
from xauusd.core.trigger_checker import TriggerChecker as XauusdTriggerChecker

from bot.commands import (
    start_command,
    nifty_command,
    xauusd_command,
    nifty_active_command,
    xauusd_active_command,
    nifty_remove_command,
    xauusd_remove_command,
    nifty_reset_command,
    xauusd_reset_command,
    price_command,
    handle_plain_text,
    opentrades_command,
    portfolio_command,
)
from bot.shared import latest_prices
from bot.alerts import AlertManager

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    # 1. Initialize databases
    await nifty_db.init_db()
    await nifty_portfolio.init_portfolio_db()
    await xauusd_db.init_db()
    await xauusd_portfolio.init_portfolio_db()
    logger.info("Databases initialized.")

    # 2. Build Telegram Application
    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start",          start_command))
    application.add_handler(CommandHandler("nifty",          nifty_command))
    application.add_handler(CommandHandler("xauusd",         xauusd_command))
    application.add_handler(CommandHandler("niftyactive",   nifty_active_command))
    application.add_handler(CommandHandler("xauusdactive",  xauusd_active_command))
    application.add_handler(CommandHandler("niftyremove",   nifty_remove_command))
    application.add_handler(CommandHandler("xauusdremove",  xauusd_remove_command))
    application.add_handler(CommandHandler("niftyreset",    nifty_reset_command))
    application.add_handler(CommandHandler("xauusdreset",   xauusd_reset_command))
    application.add_handler(CommandHandler("price",         price_command))
    application.add_handler(CommandHandler("opentrades",    opentrades_command))
    application.add_handler(CommandHandler("portfolio",     portfolio_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plain_text))

    # 3. Wire alert + signal engines
    alert_manager      = AlertManager(application)
    nifty_trigger      = NiftyTriggerChecker(alert_manager.send_signal_alert)
    xauusd_trigger     = XauusdTriggerChecker(alert_manager.send_signal_alert)

    # 4. Bridge: External threads/polling → async event loop
    loop = asyncio.get_running_loop()

    async def on_nifty_tick(ltp: float):
        latest_prices["NIFTY"] = ltp
        await nifty_trigger.check_ticks(ltp)

    async def on_xauusd_tick(ltp: float):
        latest_prices["XAUUSD"] = ltp
        await xauusd_trigger.check_ticks(ltp)

    # 5. Start Data Streams
    # 5a. Nifty (Yahoo Finance Polling in Task)
    nifty_stream = NiftyPriceStream(on_nifty_tick)
    asyncio.create_task(nifty_stream.start())
    
    # 5b. XAUUSD (Binance WebSocket in Task)
    xauusd_stream = XAUUSDPriceStream(on_xauusd_tick)
    asyncio.create_task(xauusd_stream.start())

    # 6. Schedulers (Nifty reset - assuming same time for both or shared)
    nifty_scheduler = setup_nifty_scheduler()
    nifty_scheduler.start()

    # 7. Run Telegram Bot
    logger.info("Starting Telegram Bot...")
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=["message"])
        
        logger.info("Bot is now live and polling.")
        
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Interrupt received, stopping...")
    finally:
        logger.info("Shutting down...")
        nifty_scheduler.shutdown(wait=False)
        nifty_stream.stop()
        xauusd_stream.stop()
        
        if application.updater.running:
            await application.updater.stop()
        if application.running:
            await application.stop()
        await application.shutdown()
        logger.info("Shutdown complete.")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C).")
