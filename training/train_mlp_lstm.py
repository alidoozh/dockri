import argparse, numpy as np, joblib, pandas as pd, ta
from services.price_fetcher import get_recent_minutes
from sklearn.pipeline import Pipeline
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

def build_features(df: pd.DataFrame):
    df=df.copy()
    df['close']=df['price']
    macd=ta.trend.MACD(df['close'])
    df['macd']=macd.macd(); df['macd_signal']=macd.macd_signal()
    df['ema20']=ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50']=ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    tr1=(df['high']-df['low']).abs()
    tr2=(df['high']-df['close'].shift()).abs()
    tr3=(df['low']-df['close'].shift()).abs()
    tr=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
    df['atr_pct']=(tr.rolling(14).mean()/df['close']).clip(lower=0).fillna(0)
    df['rsi']=ta.momentum.RSIIndicator(df['close'], window=14).rsi().fillna(50)
    df['vol_z']=((df['volume']-df['volume'].rolling(20).mean())/(df['volume'].rolling(20).std()+1e-9)).fillna(0).clip(-5,5)
    df.dropna(inplace=True)
    return df

def main(hours, out):
    df=get_recent_minutes(limit=hours*60)
    df=build_features(df)
    X=[]; y=[]
    closes=df['close'].values
    macd_delta=(df['macd']-df['macd_signal']).values
    ema_spread=(df['ema20']-df['ema50']).values
    for i in range(len(df)-2):
        X.append([df['rsi'].iloc[i], macd_delta[i], ema_spread[i], df['atr_pct'].iloc[i], df['vol_z'].iloc[i]])
        ret=(closes[i+2]-closes[i+1])/closes[i+1]
        y.append(max(-1.0, min(1.0, ret*100)))
    X=np.array(X); y=np.array(y)
    pipe=Pipeline([('scaler',StandardScaler()),('mlp', MLPRegressor(hidden_layer_sizes=(64,32), activation='relu', max_iter=400))])
    pipe.fit(X,y)
    joblib.dump(pipe, out)
    print("saved", out)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--hours', type=int, default=168)
    ap.add_argument('--out', type=str, default='models/mlp_lstm_model.pkl')
    args=ap.parse_args()
    main(args.hours, args.out)
