# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, stoploss_from_open
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List

class SentinelStrategyV8(IStrategy):
    """
    SentinelStrategyV8 - The 80% Profit Challenger
    - Concept: High-Frequency Volatility Breakout (Loosened Filters)
    - Target: Capturing every single micro-trend in 2025
    - Exit: Hyper-Scalping ROI
    """
    
    INTERFACE_VERSION = 3

    # 수익률 80%를 위해 회전율을 극대화하는 초단기 ROI
    minimal_roi = {
        "0": 0.10,      # 10% 수익 시 즉시 익절
        "30": 0.05,     # 30분 후 5%
        "60": 0.02,     # 1시간 후 2%
        "120": 0.01     # 2시간 후 1% (익절 순환 가속화)
    }

    # 손절 라인: 2025년 휩소를 견디기 위해 V3 수준으로 복귀
    stoploss = -0.10

    # 트레일링 스탑: 짧은 수익도 놓치지 않도록 매우 타이트하게 설정
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    timeframe = '1h'
    can_short: bool = True

    # 하이퍼파라미터: 2025년 시장에 맞춘 '공격적' 설정
    buy_adx_min = IntParameter(15, 35, default=20, space="buy")
    buy_volume_mult = DecimalParameter(0.8, 2.0, default=1.1, space="buy")

    startup_candle_count: int = 200

    def leverage(self, pair: str, current_time: str, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str, side: str,
                 **kwargs) -> float:
        # 80% 달성을 위해 5배 레버리지로 상향 (공격적 운영)
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_lowerband'] = bollinger['lower']
        
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=30).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long: 필터를 완화하여 더 많은 기회 포착
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ema200']) & 
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult.value) &
                (dataframe['adx'] > self.buy_adx_min.value)
            ),
            ['enter_long', 'enter_tag']] = (1, 'agg_long_v8')

        # Short: 필터를 완화하여 더 많은 기회 포착
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['ema200']) & 
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult.value) &
                (dataframe['adx'] > self.buy_adx_min.value)
            ),
            ['enter_short', 'enter_tag']] = (1, 'agg_short_v8')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 2025년은 빠른 탈출이 생명
        dataframe.loc[(dataframe['rsi'] > 80), 'exit_long'] = 1
        dataframe.loc[(dataframe['rsi'] < 20), 'exit_short'] = 1
        return dataframe
