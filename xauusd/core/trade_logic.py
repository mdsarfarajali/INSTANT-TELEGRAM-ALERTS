import logging

logger = logging.getLogger(__name__)

def calculate_trade_params(level_price: float, level_type: str):
    """
    XAUUSD Trade Logic:
    CALL: Target = +5.0, SL = -5.0
    PUT:  Target = -5.0, SL = +5.0
    """
    offset = 5.0  # Default $5 move for Gold
    
    if level_type == "CALL":
        target = level_price + offset
        sl     = level_price - offset
    elif level_type == "PUT":
        target = level_price - offset
        sl     = level_price + offset
    else: # TOUCH
        target = level_price + offset
        sl     = level_price - offset
        
    return {
        "instrument": "XAUUSD",
        "type": level_type,
        "entry": level_price,
        "target": round(target, 2),
        "sl": round(sl, 2)
    }
