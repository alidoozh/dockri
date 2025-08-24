import gymnasium as gym
import numpy as np

class TradingEnv(gym.Env):
    metadata = {"render.modes": ["human"]}
    def __init__(self, df):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.t=50
        self.position=0
        self.entry=0.0
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(3) # 0 hold,1 long,2 flat

    def _obs(self):
        row = self.df.iloc[self.t]
        return np.array([row['close'], row['rsi'], row['macd']-row['macd_signal'], row['ema20']-row['ema50'], row['atr_pct'], row['vol_z']], dtype=np.float32)

    def step(self, action):
        reward = 0.0
        price = float(self.df.iloc[self.t]['close'])
        if action==1 and self.position==0:
            self.position=1; self.entry=price
        elif action==2 and self.position==1:
            reward = (price-self.entry)/self.entry
            self.position=0; self.entry=0.0
        self.t+=1
        terminated = self.t>=len(self.df)-1
        return self._obs(), reward, terminated, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.t=50; self.position=0; self.entry=0.0
        return self._obs(), {}
