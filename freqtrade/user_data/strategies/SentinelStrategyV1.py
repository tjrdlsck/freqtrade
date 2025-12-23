# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, stoploss_from_open
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List

class SentinelStrategyV1(IStrategy):
    """
    SentinelStrategyV1
    - Concept: Basic RSI Strategy for Futures
    - Author: Project Sentinel
    """
    
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check freqtrade documentation for details.
    INTERFACE_VERSION = 3

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False

    # Timeframe
    timeframe = '5m'

    # Can this strategy go short?
    can_short: bool = True

    # Hyperspace parameters
    buy_rsi = IntParameter(10, 40, default=30, space="buy")
    sell_rsi = IntParameter(60, 90, default=70, space="sell")

    # Run "populate_indicators" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    def leverage(self, pair: str, current_time: str, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str, side: str,
                 **kwargs) -> float:
        """
        Customize leverage for each new trade.
        """
        return 3.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different technical indicators to the given DataFrame
        """
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        """
        
        # Long Entry
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        # Short Entry
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        """
        
        # Long Exit
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
            
        # Short Exit
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'exit_short'] = 1

        return dataframe
