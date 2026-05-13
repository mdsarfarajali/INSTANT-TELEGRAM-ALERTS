import datetime
import logging
from telegram.ext import Application
from config.settings import settings

logger = logging.getLogger(__name__)


def format_signal_message(trade: dict) -> str:
    """
    Returns a Markdown-formatted Telegram signal message.
    """
    instrument = trade.get("instrument", "TRACKER")
    emoji = "🟢" if trade["type"] == "CALL" else "🔴"
    
    # Get time from trade or now
    timestamp = trade.get("time", datetime.datetime.now().strftime("%H:%M:%S"))
    
    msg = (
        f"🚨 *{trade['type']} SIGNAL*\n\n"
        f"{emoji} *{instrument} HIT:* `{trade['entry']}`\n"
        f"📌 *ENTRY:*    `{trade['entry']}`\n"
        f"🎯 *TARGET:*  `{trade['target']}`\n"
        f"🛑 *SL:*         `{trade['sl']}`\n"
        f"🕐 *TIME:*     `{timestamp}`"
    )
    return msg

def format_exit_message(trade: dict) -> str:
    instrument = trade.get("instrument", "TRACKER")
    exit_status = trade.get("exit_status")
    pnl = trade.get("pnl", 0)
    
    emoji = "🎯" if exit_status == "PROFIT" else "🛑"
    
    msg = (
        f"{emoji} *{exit_status} HIT!*\n\n"
        f"📈 *{instrument} {trade['type']}*\n"
        f"💰 *P&L:* `{pnl:+} Points`\n"
        f"📌 *Exit Price:* `{trade['exit_price']}`"
    )
    return msg


class AlertManager:
    def __init__(self, application: Application):
        self.application = application

    async def send_signal_alert(self, trade: dict):
        """Sends the formatted signal or exit message to the admin chat."""
        if "exit_status" in trade:
            message = format_exit_message(trade)
        else:
            message = format_signal_message(trade)
        try:
            await self.application.bot.send_message(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"Alert sent: {trade.get('instrument')} {trade['type']} @ {trade['entry']}")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
