import logging
from telegram import Update
from telegram.ext import ContextTypes
import nifty.storage.database as nifty_db
import xauusd.storage.database as xauusd_db
import nifty.storage.portfolio as nifty_portfolio
import xauusd.storage.portfolio as xauusd_portfolio
from bot.shared import latest_prices
from bot.graph_generator import generate_portfolio_chart
from config.settings import settings

logger = logging.getLogger(__name__)


def is_admin(update: Update) -> bool:
    return update.effective_user.id == settings.TELEGRAM_ADMIN_ID


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Multi-Instrument Signal Bot (Updated Format)*\n\n"
        "📈 *NIFTY:* Send up to 4 prices. Order: `PUT, PUT, CALL, CALL`\n"
        "/nifty — Set levels (e.g., `/nifty 24800 24700 0 24500`)\n"
        "/niftyactive — Show active levels\n"
        "/niftyremove <price> — Deactivate level\n"
        "/niftyreset — Clear all levels\n\n"
        "🟡 *XAUUSD:* Send up to 2 prices. Order: `CALL, PUT`\n"
        "/xauusd — Set levels (e.g., `/xauusd 2350 2360` or `/xauusd 0 2360`)\n"
        "/xauusdactive — Show active levels\n"
        "/xauusdremove <price> — Deactivate level\n"
        "/xauusdreset — Clear all levels\n\n"
        "📈 *Paper Trading & Portfolio:*\n"
        "/opentrades — View all active virtual trades\n"
        "/portfolio — View P&L chart and stats\n\n"
        "🔍 *Check Prices:*\n"
        "/price — Show current LTP for NIFTY & Gold",
        parse_mode="Markdown"
    )


async def nifty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    # Extract all numbers from the message
    raw_text = update.message.text.replace("/nifty", "").strip()
    # Split by any whitespace or newline
    parts = raw_text.split()
    
    if not parts:
        await update.message.reply_text("Please provide prices.\nExample: `/nifty 24800 24700 0 24500`", parse_mode="Markdown")
        return

    # NIFTY Order: 0:PUT, 1:PUT, 2:CALL, 3:CALL
    nifty_types = ["PUT", "PUT", "CALL", "CALL"]
    added = []
    
    for i, part in enumerate(parts[:4]): # Max 4 levels
        try:
            price = float(part)
            if price <= 0: continue # Skip if 0 or negative
            
            level_type = nifty_types[i]
            await nifty_db.add_level(price, level_type)
            added.append(f"  • {price} ({level_type})")
        except ValueError:
            continue

    if added:
        total_count = await nifty_db.get_today_level_count()
        await nifty_db.update_daily_history(total_count)
        await update.message.reply_text(f"✅ *NIFTY Added:*\n" + "\n".join(added), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No valid prices found.")


async def xauusd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    raw_text = update.message.text.replace("/xauusd", "").strip()
    parts = raw_text.split()
    
    if not parts:
        await update.message.reply_text("Please provide prices.\nExample: `/xauusd 2350 2360` (CALL then PUT)", parse_mode="Markdown")
        return
    
    # Gold Order: 0:CALL, 1:PUT
    gold_types = ["CALL", "PUT"]
    added = []
    
    for i, part in enumerate(parts[:2]): # Max 2 levels
        try:
            price = float(part)
            if price <= 0: continue
            
            level_type = gold_types[i]
            await xauusd_db.add_level(price, level_type)
            added.append(f"  • {price} ({level_type})")
        except ValueError:
            continue
            
    if added:
        total_count = await xauusd_db.get_today_level_count()
        await xauusd_db.update_daily_history(total_count)
        await update.message.reply_text(f"✅ *GOLD Added:*\n" + "\n".join(added), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No valid prices found.")


async def _active_levels(update: Update, db_module, instrument_name: str):
    levels = await db_module.get_active_levels()
    if not levels:
        await update.message.reply_text(f"📭 No active {instrument_name} levels.")
        return

    lines = [f"  • `{lvl['price']}` ({lvl['level_type']})" for lvl in levels]
    text = f"📋 *Active {instrument_name} Levels:*\n" + "\n".join(lines)
    await update.message.reply_text(text, parse_mode="Markdown")


async def nifty_active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _active_levels(update, nifty_db, "NIFTY")


async def xauusd_active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _active_levels(update, xauusd_db, "XAUUSD")


async def _remove_level(update: Update, context, db_module, instrument_name: str):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text(f"Usage: /{instrument_name.lower()}remove <price>")
        return

    try:
        price = float(context.args[0])
        await db_module.remove_level_by_price(price)
        await update.message.reply_text(f"🗑 {instrument_name} Level `{price}` deactivated.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Invalid price.")


async def nifty_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _remove_level(update, context, nifty_db, "NIFTY")


async def xauusd_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _remove_level(update, context, xauusd_db, "XAUUSD")


async def _reset_levels(update: Update, db_module, instrument_name: str):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    await db_module.reset_levels()
    await update.message.reply_text(f"🔄 All {instrument_name} levels cleared.")


async def nifty_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _reset_levels(update, nifty_db, "NIFTY")


async def xauusd_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _reset_levels(update, xauusd_db, "XAUUSD")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nifty_price = latest_prices.get("NIFTY")
    gold_price  = latest_prices.get("XAUUSD")
    
    nifty_text = f"`{nifty_price}`" if nifty_price else "_Waiting for tick..._"
    gold_text  = f"`{gold_price}`"  if gold_price  else "_Waiting for tick..._"
    
    msg = (
        "📊 *Live Market Prices*\n\n"
        f"📈 *NIFTY:* {nifty_text}\n"
        f"🟡 *GOLD:*  {gold_text}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
        
    await update.message.reply_text(
        "❌ *Oops! You sent the price in a separate message.*\n\n"
        "You must type the command **AND** the price together in the **SAME** message.\n\n"
        "✅ *Correct Way for Gold:*\n"
        "`/xauusd 2350 2360` (CALL first, then PUT)\n\n"
        "✅ *Correct Way for Nifty:*\n"
        "`/nifty 24800 24700 0 24500`\n\n"
        "Please type it exactly like the examples above!",
        parse_mode="Markdown"
    )

async def opentrades_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nifty_trades = await nifty_portfolio.get_open_trades()
    gold_trades = await xauusd_portfolio.get_open_trades()
    
    if not nifty_trades and not gold_trades:
        await update.message.reply_text("📭 No active virtual trades currently running.")
        return
        
    lines = ["📊 *Open Virtual Trades:*\n"]
    for t in nifty_trades:
        lines.append(f"📈 *NIFTY {t['trade_type']}* | Entry: `{t['entry_price']}` | TP: `{t['target_price']}` | SL: `{t['sl_price']}`")
    for t in gold_trades:
        lines.append(f"🟡 *GOLD {t['trade_type']}* | Entry: `{t['entry_price']}` | TP: `{t['target_price']}` | SL: `{t['sl_price']}`")
        
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nifty_closed = await nifty_portfolio.get_all_closed_trades()
    gold_closed = await xauusd_portfolio.get_all_closed_trades()
    
    total_trades = len(nifty_closed) + len(gold_closed)
    
    if total_trades == 0:
        await update.message.reply_text("📉 No closed trades in the portfolio yet.")
        return
        
    await update.message.reply_text("⏳ Generating your Portfolio P&L Chart...")
    
    # Generate graph
    buf, current_pnl = await generate_portfolio_chart(nifty_closed, gold_closed)
    
    caption = (
        f"📊 *Paper Trading Portfolio*\n\n"
        f"✅ Total Trades: `{total_trades}`\n"
        f"💰 Cumulative P&L: `{current_pnl:+} Points`\n"
        f"(+50 points for profit, -50 points for loss)"
    )
    
    await update.message.reply_photo(photo=buf, caption=caption, parse_mode="Markdown")
