import pandas as pd, ta

def macd_features(df: pd.DataFrame):
    close=df['price']
    m=ta.trend.MACD(close)
    return pd.DataFrame({
        'macd': m.macd(),
        'macd_signal': m.macd_signal(),
        'macd_hist': m.macd_diff()
    })
