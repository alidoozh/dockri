import argparse, ta
from services.price_fetcher import get_recent_minutes
from training.TradingEnv import TradingEnv

def build_df(hours):
    import pandas as pd
    df=get_recent_minutes(limit=hours*60)
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

def main(hours, timesteps, out):
    try:
        from stable_baselines3 import SAC
        from stable_baselines3.common.vec_env import DummyVecEnv
    except Exception:
        print("stable-baselines3 not available. Install optional deps first.")
        return
    df=build_df(hours)
    env=DummyVecEnv([lambda: TradingEnv(df)])
    model=SAC("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=timesteps)
    model.save(out)
    print("saved", out)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--hours', type=int, default=168)
    ap.add_argument('--timesteps', type=int, default=50000)
    ap.add_argument('--out', type=str, default='models/sac_model')
    args=ap.parse_args()
    main(args.hours, args.timesteps, args.out)
