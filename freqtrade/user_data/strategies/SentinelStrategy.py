# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, stoploss_from_open
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class SentinelStrategy(IStrategy):
    """
    SentinelStrategyV11 - The Robust Explorer
    - Based on V10
    - Goal: Find the 'Plateau' of stability through comprehensive parameter optimization
    - Improvements:
        1. Added RSI & EWO filters for Long Entry (to avoid false breakouts in bear markets)
        2. Enhanced Timeout Logic (Zombie trade killer)
        3. All key variables are exposed as Hyperopt Parameters
    """
    
    INTERFACE_VERSION = 3

    # ROI: Default low for safety, but strategy relies heavily on custom exit & trailing stop
    minimal_roi = {
        "0": 0.10,
        "30": 0.05,
        "60": 0.02,
        "120": 0.01
    }

    # Hard Stoploss: Safety net
    stoploss = -0.25 

    # Trailing Stop: Can be optimized via configuration, but kept standard here
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True

    timeframe = '1h'
    can_short: bool = True
    
    startup_candle_count: int = 200

    # -------------------------------------------------------------------------
    # 1. Long Parameters (Optimization Target: OPEN)
    # -------------------------------------------------------------------------
    
    # [Entry - Trend Strength]
    buy_adx_long = IntParameter(15, 50, default=15, space="buy", optimize=True)
    buy_volume_mult_long = DecimalParameter(1.0, 5.0, default=1.102, space="buy", optimize=True)
    
    # [Entry - Overbought/Oversold Protection] *NEW*
    # RSI가 이 값보다 낮아야 진입 (너무 높은 곳에서 물리지 않기 위함)
    buy_rsi_max_long = IntParameter(50, 95, default=88, space="buy", optimize=True)
    
    # [Entry - Momentum/Wave] *NEW*
    # EWO가 이 값보다 커야 진입 (상승 파동 확인)
    buy_ewo_min_long = DecimalParameter(-5.0, 10.0, default=-4.109, space="buy", optimize=True)

    # [Risk - Stoploss]
    stoploss_atr_mult_long = DecimalParameter(1.0, 3.5, default=1.426, space="sell", optimize=True)
    
    # [Exit - Timeout]
    # 1. Basic Timeout: 수익이 저조할 때 자르는 시간
    timeout_hours_long = IntParameter(3, 24, default=3, space="sell", optimize=True)
    # 2. Threshold: Timeout 시 수익률 기준 (이것보다 낮으면 자름)
    timeout_profit_long = DecimalParameter(-0.05, 0.05, default=0.038, decimals=3, space="sell", optimize=True)


    # -------------------------------------------------------------------------
    # 2. Short Parameters (Optimization Target: LOCKED)
    # -------------------------------------------------------------------------
    # V9/V10에서 검증된 값 고정
    
    buy_adx_short = IntParameter(10, 35, default=17, space="buy", optimize=False)
    buy_volume_mult_short = DecimalParameter(1.0, 3.0, default=1.879, space="buy", optimize=False)
    stoploss_atr_mult_short = DecimalParameter(2.0, 5.0, default=3.8, space="sell", optimize=False)
    timeout_hours_short = IntParameter(4, 24, default=14, space="sell", optimize=False)


    def leverage(self, pair: str, current_time: str, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str, side: str,
                 **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Trend
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # EWO (Elliott Wave Oscillator)
        dataframe['sma_5'] = ta.SMA(dataframe, timeperiod=5)
        dataframe['sma_35'] = ta.SMA(dataframe, timeperiod=35)
        dataframe['ewo'] = (dataframe['sma_5'] - dataframe['sma_35'])
        
        # Volatility
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_lowerband'] = bollinger['lower']
        
        # Volume
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=30).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ---------------------------------------------------------------------
        # Long Entry: Enhanced Logic
        # ---------------------------------------------------------------------
        dataframe.loc[
            (
                (dataframe['close'] > dataframe['ema200']) & 
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult_long.value) &
                (dataframe['adx'] > self.buy_adx_long.value) &
                # New Filters for Optimization
                (dataframe['rsi'] < self.buy_rsi_max_long.value) & # 과열권 추격 매수 방지
                (dataframe['ewo'] > self.buy_ewo_min_long.value)   # 상승 파동 확인
            ),
            ['enter_long', 'enter_tag']] = (1, 'sentinel_long')

        # ---------------------------------------------------------------------
        # Short Entry: Legacy Logic (Locked)
        # ---------------------------------------------------------------------
        dataframe.loc[
            (
                (dataframe['close'] < dataframe['ema200']) & 
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > dataframe['volume_mean'] * self.buy_volume_mult_short.value) &
                (dataframe['adx'] > self.buy_adx_short.value)
            ),
            ['enter_short', 'enter_tag']] = (1, 'sentinel_short')

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI Extremes
        dataframe.loc[(dataframe['rsi'] > 80), 'exit_long'] = 1
        dataframe.loc[(dataframe['rsi'] < 20), 'exit_short'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        if np.isnan(last_candle['atr']):
            return -0.10
        
        if trade.is_short:
            atr_mult = self.stoploss_atr_mult_short.value
        else:
            atr_mult = self.stoploss_atr_mult_long.value
            
        stoploss_ratio = (last_candle['atr'] * atr_mult) / last_candle['close']
        stoploss_ratio = max(0.02, min(0.15, stoploss_ratio))
        
        return -stoploss_ratio

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        
        if trade.is_short:
            # Short: Legacy logic
            if (current_time - trade.open_date_utc).total_seconds() > (self.timeout_hours_short.value * 3600):
                if current_profit < 0.01:
                     return "timeout_exit"
        else:
            # Long: Enhanced logic with optimization target
            # 파라미터화된 시간과 수익률 임계값 사용
            if (current_time - trade.open_date_utc).total_seconds() > (self.timeout_hours_long.value * 3600):
                if current_profit < self.timeout_profit_long.value:
                     return "timeout_exit"
        
        return None
