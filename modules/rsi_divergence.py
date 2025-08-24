import pandas as pd, ta

def rsi_and_divergence(df: pd.DataFrame, window: int = 14):
    x = df.copy()
    close = x['price']
    rsi = ta.momentum.RSIIndicator(close, window=window).rsi()
    x['rsi'] = rsi
    x['ll_price'] = close < close.shift(1)
    x['hl_rsi'] = rsi > rsi.shift(1)
    x['bull_div'] = (x['ll_price'] & x['hl_rsi']).astype(int)
    x['bear_div'] = ((~x['ll_price']) & (~x['hl_rsi'])).astype(int)
    return x[['rsi','bull_div','bear_div']]
