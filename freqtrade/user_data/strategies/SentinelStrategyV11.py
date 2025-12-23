# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, stoploss_from_open
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List

class SentinelStrategyV11(IStrategy):
    """
    SentinelStrategyV11 - The Balanced Force
    - Focus: Maximizing Long Alpha & Minimizing Short Beta
    - Mechanism: Asymmetric Leverage & Volume-based Exhaustion Exit
    - Target: High Compound ROI with minimal Drawdown
    """
    
    INTERFACE_VERSION = 3

    # 수익률 80% 이상을 위한 공격적인 ROI 테이블
    minimal_roi = {
        "0": 0.15,
        "30": 0.08,
        "120": 0.04,
        "240": 0.02
    }

    # 시스템 손절: V10보다 소폭 여유를 주되 트레일링으로 관리
    stoploss = -0.07

    # 트레일링 스탑: 수익 보존의 핵심
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    timeframe = '1h'
    can_short: bool = True

    # 하이퍼파라미터
    buy_adx_min = IntParameter(20, 40, default=26, space="buy")
    volume_mult = DecimalParameter(1.1, 2.5, default=1.3, space="buy")

    startup_candle_count: int = 200

    def leverage(self, pair: str, current_time: str, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str, side: str,
                 **kwargs) -> float:
        # 비대칭 레버리지 전략: 롱은 공격적으로, 숏은 방어적으로
        if side == 'long':
            return 5.0
        return 2.5

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_lowerband'] = bollinger['lower']
        
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=30).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long Entry: 200일선 위 + 수급 확증
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ema200']) & 
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.volume_mult.value) &
                (dataframe['adx'] > self.buy_adx_min.value) &
                (dataframe['rsi'] < 75)
            ),
            ['enter_long', 'enter_tag']] = (1, 'power_long_v11')

        # Short Entry: 200일선 아래 + 이중 추세 확증
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['ema200']) & 
                (dataframe['ema50'] < dataframe['ema200']) & 
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.volume_mult.value) &
                (dataframe['adx'] > self.buy_adx_min.value) &
                (dataframe['rsi'] < 40)
            ),
            ['enter_short', 'enter_tag']] = (1, 'protected_short_v11')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 힘이 빠질 때 조기 탈출 (Exhaustion Exit)
        dataframe.loc[
            (qtpylib.crossed_below(dataframe['close'], dataframe['ema20'])),
            ['exit_long', 'exit_tag']] = (1, 'long_exhaustion')

        dataframe.loc[
            (qtpylib.crossed_above(dataframe['close'], dataframe['ema20'])),
            ['exit_short', 'exit_tag']] = (1, 'short_exhaustion')

        return dataframe
