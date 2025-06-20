def calculate_take_profit(entry_price, atr, multiplier=1.2):
    return round(entry_price + atr * multiplier, 5)


def calculate_stop_loss(entry_price, atr, trailing=False, current_price=None):
    if trailing and current_price:
        trailing_distance = atr * 1.0
        return round(current_price - trailing_distance, 5)
    else:
        return round(entry_price - atr * 1.0, 5)


def should_exit_trade(entry_price, current_price, tp_price, sl_price):
    if current_price >= tp_price:
        return True, "Take Profit atingido"
    elif current_price <= sl_price:
        return True, "Stop Loss atingido"
    return False, ""
