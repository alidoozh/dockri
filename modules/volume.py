import pandas as pd

def volume_features(df: pd.DataFrame):
    v=df['volume'].fillna(0)
    vma=v.rolling(20).mean()
    vstd=v.rolling(20).std()
    z=((v-vma)/(vstd+1e-9)).clip(-5,5).fillna(0)
    return pd.DataFrame({'vol_z':z, 'vol_ma':vma.fillna(0)})
