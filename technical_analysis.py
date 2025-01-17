import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from dataclasses import dataclass
import talib
from scipy import stats

@dataclass
class TechnicalIndicators:
    #container for technical indicators
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    atr: float
    adx: float
    obv: float
    stoch_k: float
    stoch_d: float

class TechnicalAnalyzer:
    def __init__(self, 
                 rsi_period: int = 14, #maybe change later
                 macd_fast: int = 12,
                 macd_slow: int = 26,
                 macd_signal: int = 9,
                 bb_period: int = 20,
                 bb_std: int = 2,
                 atr_period: int = 14,
                 adx_period: int = 14,
                 stoch_period: int = 14,
                 stoch_slowk: int = 3,
                 stoch_slowd: int = 3):
        #initialize technical analysis parameters
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.stoch_period = stoch_period
        self.stoch_slowk = stoch_slowk
        self.stoch_slowd = stoch_slowd