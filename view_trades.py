import sqlite3
import os

def show_portfolio(db_path, name):
    if not os.path.exists(db_path):
        print(f"\n[!] {name} database file not found yet. (Wait for a trade to trigger!)")
        return

    print(f"\n{'='*20} {name} PORTFOLIO {'='*20}")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if not cursor.fetchone():
            print(f"Table 'trades' not found in {name} DB.")
            conn.close()
            return

        cursor.execute("SELECT * FROM trades ORDER BY opened_at DESC")
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 No trades found in history.")
        else:
            # Header
            print(f"{'ID':<4} | {'Type':<6} | {'Entry':<10} | {'Status':<8} | {'PnL Pts':<8} | {'Opened At'}")
            print("-" * 75)
            
            for row in rows:
                pnl = row['pnl_points']
                pnl_str = f"{pnl:+.1f}" if pnl is not None else "0.0"
                
                print(f"{row['id']:<4} | "
                      f"{row['trade_type']:<6} | "
                      f"{row['entry_price']:<10.2f} | "
                      f"{row['status']:<8} | "
                      f"{pnl_str:<8} | "
                      f"{row['opened_at'][:19]}")
        conn.close()
    except Exception as e:
        print(f"❌ Error reading {name}: {e}")

if __name__ == "__main__":
    show_portfolio("nifty/storage/portfolio.db", "NIFTY")
    show_portfolio("xauusd/storage/portfolio.db", "GOLD")
    print("\n" + "="*52)
    print("Tip: Use /portfolio in Telegram to see the visual graph!")
