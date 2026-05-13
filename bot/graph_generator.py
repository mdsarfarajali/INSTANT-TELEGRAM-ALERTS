import matplotlib.pyplot as plt
import io

async def generate_portfolio_chart(nifty_trades, gold_trades):
    # Merge and sort trades by closed_at
    all_trades = nifty_trades + gold_trades
    all_trades.sort(key=lambda x: x["closed_at"])

    cumulative_pnl = [0]
    labels = ["Start"]
    
    current_pnl = 0
    for idx, trade in enumerate(all_trades):
        current_pnl += trade["pnl_points"]
        cumulative_pnl.append(current_pnl)
        labels.append(f"T{idx+1}")

    # Set up the plot
    plt.figure(figsize=(10, 5))
    
    # Define colors based on point value
    colors = ['green' if p >= 0 else 'red' for p in cumulative_pnl]
    
    plt.plot(labels, cumulative_pnl, marker='o', linestyle='-', color='blue', linewidth=2)
    
    # Fill area under/over the line
    plt.fill_between(range(len(cumulative_pnl)), cumulative_pnl, 0, 
                     where=[p >= 0 for p in cumulative_pnl], 
                     facecolor='green', alpha=0.2, interpolate=True)
                     
    plt.fill_between(range(len(cumulative_pnl)), cumulative_pnl, 0, 
                     where=[p < 0 for p in cumulative_pnl], 
                     facecolor='red', alpha=0.2, interpolate=True)
    
    plt.axhline(0, color='black', linewidth=1.5, linestyle='--')
    plt.title("Paper Trading Portfolio (Cumulative P&L in Points)", fontsize=14, fontweight='bold')
    plt.xlabel("Trades (Chronological)", fontsize=12)
    plt.ylabel("Points (+50/-50 per trade)", fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close()
    
    return buf, current_pnl
