import datetime


def calculate_trade_params(level_price: float, level_type: str) -> dict:
    """
    CALL: ENTRY = level, TARGET = +50, SL = -50
    PUT:  ENTRY = level, TARGET = -50, SL = +50
    """
    entry = level_price
    level_type = level_type.upper()

    if level_type == "CALL":
        target = entry + 50
        sl = entry - 50
    else:  # PUT
        target = entry - 50
        sl = entry + 50

    return {
        "instrument": "NIFTY",
        "type": level_type,
        "entry": entry,
        "target": target,
        "sl": sl,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
    }


