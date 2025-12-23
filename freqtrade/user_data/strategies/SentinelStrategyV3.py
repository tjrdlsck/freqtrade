# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, stoploss_from_open
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List

class SentinelStrategyV3(IStrategy):
    """
    SentinelStrategyV3 - Volatility Squeeze & Volume Breakout
    - Timeframe: 1h
    - Concept: Enter on high volume breakout after volatility squeeze
    - Exit: 100% Trailing Stop & Dynamic ROI
    """
    
    INTERFACE_VERSION = 3

    # 수익 극대화를 위한 ROI 설정
    minimal_roi = {
        "0": 0.25,      # 25% 수익 시 익절
        "200": 0.15,    # 약 8시간 후 15% 수익 시 익절
        "400": 0.08,    # 약 16시간 후 8% 수익 시 익절
        "1440": 0.04    # 24시간 후 4% 수익 시 익절
    }

    # 손절 라인: ATR 기반 동적 손절을 사용하되, 최대 마지노선 설정
    stoploss = -0.10

    # 트레일링 스탑: V3의 핵심 (수익 추격)
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True

    timeframe = '1h'
    can_short: bool = True

    # 최적화 변수
    buy_adx = IntParameter(20, 45, default=30, space="buy")
    buy_volume_mult = DecimalParameter(1.0, 3.0, default=1.5, space="buy")

    startup_candle_count: int = 200

    def leverage(self, pair: str, current_time: str, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str, side: str,
                 **kwargs) -> float:
        return 3.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 이평선
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)

        # 볼린저 밴드
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_width'] = (dataframe['bb_upperband'] - dataframe['bb_lowerband']) / dataframe['ema20']

        # 변동성 압축(Squeeze) 확인: 최근 20캔들 중 밴드폭이 최소 수준인지 확인
        dataframe['bb_sqz'] = dataframe['bb_width'] < dataframe['bb_width'].rolling(window=20).mean()

        # 거래량 평균
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=30).mean()

        # RSI & ADX
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long: 200일선 위 + 변동성 돌파 + 거래량 실림
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ema200']) & 
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult.value) &
                (dataframe['adx'] > self.buy_adx.value) &
                (dataframe['bb_sqz'] == True) & # 압축 상태에서 돌파
                (dataframe['rsi'] < 75)
            ),
            ['enter_long', 'enter_tag']] = (1, 'long_breakout')

        # Short: 200일선 아래 + 변동성 하락 돌파 + 거래량 실림
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['ema200']) &
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult.value) &
                (dataframe['adx'] > self.buy_adx.value) &
                (dataframe['bb_sqz'] == True) &
                (dataframe['rsi'] > 25)
            ),
            ['enter_short', 'enter_tag']] = (1, 'short_breakout')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # V3 전략은 인디케이터 기반 청산을 사용하지 않고 ROI와 Trailing Stop에만 의존함
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0
        return dataframe
