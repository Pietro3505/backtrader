import backtrader as bt
import math
from calculate_indicators import params

class EMAVolMACDStrategy(bt.Strategy):
    params = dict(
        donchian_period=params['emavolmacd_donchian_period'],
        risk_reward_ratio=params['emavolmacd_risk_reward_ratio'],
        ema_period=params['emavolmacd_ema_period'],
        macd_fast=params['emavolmacd_macd_fast'],
        macd_slow=params['emavolmacd_macd_slow'],
        macd_signal=params['emavolmacd_macd_signal']
    )

    def __init__(self):
        super(EMAVolMACDStrategy, self).__init__()
        
        # Indicators
        self.ema = bt.indicators.EMA(self.data.close, period=self.p.ema_period)
        self.vol_short = bt.indicators.SMA(self.data.volume, period=params['volume_short_period'])
        self.vol_long = bt.indicators.SMA(self.data.volume, period=params['volume_long_period'])
        self.volume_osc = (self.vol_short - self.vol_long) / self.vol_long
        
        # MACD with custom parameters
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.macd_fast,
            period_me2=self.p.macd_slow,
            period_signal=self.p.macd_signal
        )
        self.macd_hist = self.macd.macd - self.macd.signal
        self.macd_hist_prev = self.macd_hist(-1)  # Previous value
        
        self.donchian_low = bt.indicators.Lowest(self.data.low, period=self.p.donchian_period)
        
        # Trade tracking
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.take_price = None

    def next(self):
        # Cancel any pending orders
        if self.order:
            return

        # Entry conditions
        if not self.position:
            if self._buy_signal():
                self._enter_trade()
        
        # Exit conditions
        else:
            if self._exit_signal():
                self._close_trade()

    def _buy_signal(self):
        return (self.data.close[0] > self.ema[0] and
                #self.volume_osc[0] > 0 and
                self.macd_hist_prev[0] < 0 and 
                self.macd_hist[0] > 0)

    def _enter_trade(self):
        # Calculate position size using 100% equity
        total_value = self.broker.getvalue() * 0.85
        price = self.data.close[0]
        size = total_value / price
        
        self.entry_price = price
        self.stop_price = self.donchian_low[0]
        risk = self.entry_price - self.stop_price
        self.take_price = self.entry_price + (risk * self.p.risk_reward_ratio)
        
        self.order = self.buy(size=size)
        self.log(f'BUY ORDER: {size:.2f} shares @ {price:.2f}')

    def _exit_signal(self):
        return (self.data.close[0] <= self.stop_price or 
                self.data.close[0] >= self.take_price)

    def _close_trade(self):
        self.order = self.close()
        self.log(f'CLOSE ORDER: Position @ {self.data.close[0]:.2f}')
        self._reset_trade_vars()

    def _reset_trade_vars(self):
        self.entry_price = None
        self.stop_price = None
        self.take_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.size:.2f} @ {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED: {order.executed.size:.2f} @ {order.executed.price:.2f}')
            self.order = None

    def log(self, txt):
        print(f'{self.datetime.date().isoformat()}: {txt}')

# 5 ema 13 sma mit 100 ema als filter 10 ema 20 sma tages kein+mit-20 40 50 100  
# 200/100 ema filter macd risk reward 1.5 mit und ohne null linie

class EMACrossoverStrategy(bt.Strategy):
    params = dict(
        ema_fast=params['emacrossover_ema_fast'],
        sma_medium=params['emacrossover_sma_medium'],
        ema_slow=params['emacrossover_ema_slow'],
        risk_reward=params['emacrossover_risk_reward'],
        trail_stop=params['emacrossover_trail_stop']
    )

    def __init__(self):
        # Trend filter (200-period EMA)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=self.p.ema_slow)
        
        # Crossover indicators
        self.ema_fast = bt.indicators.EMA(self.data.close, period=self.p.ema_fast)
        self.sma_medium = bt.indicators.SMA(self.data.close, period=self.p.sma_medium)
        
        # Crossover signals
        self.crossover = bt.indicators.CrossOver(self.ema_fast, self.sma_medium)
        

        # Trade management variables
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.take_price = None

    def next(self):
        if self.order:
            return  # Wait for pending order execution
        
        # Trend direction check
        in_uptrend = self.data.close > self.ema_slow
        in_downtrend = self.data.close < self.ema_slow

        # Long entry condition
        if not self.position:
            if self.crossover > 0:
                self.entry_price = self.data.close[0]
                size = (self.broker.getvalue() * 0.85 )/ self.entry_price
                risk = self.entry_price - self.data.low[0]
                self.stop_price = self.entry_price - risk
                self.take_price = self.entry_price + (risk * self.p.risk_reward)
                self.order = self.buy(size=size)
                

        # Exit conditions for long position
        elif self.position.size > 0:
            if self.data.close[0] <= self.stop_price or self.data.close[0] >= self.take_price:
                self.order = self.close()
                
       

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'LONG ENTRY: {order.executed.size:.2f} @ {order.executed.price:.2f}')
            else:
                self.log(f'POSITION CLOSED: PnL {order.executed.pnl:.2f}')
            self.order = None
            self.entry_price = None

    def log(self, txt):
        dt = self.datas[0].datetime.date(0).isoformat()
        print(f'{dt}: {txt}')


class EMAMACDStrategy(bt.Strategy):
    params = dict(
        ema_period=params['emamacd_ema_period'],
        macd_fast=params['emamacd_macd_fast'],
        macd_slow=params['emamacd_macd_slow'],
        macd_signal=params['emamacd_macd_signal'],
        risk_reward=params['emamacd_risk_reward'],
        donchian_period=params['emamacd_donchian_period']
    )

    def __init__(self):
        # Trend filter (200 EMA)
        self.ema200 = bt.indicators.EMA(self.data.close, period=self.p.ema_period)
        
        # MACD indicators with SMA for fast line
        self.macd_fast_sma = bt.indicators.SMA(self.data.close, period=self.p.macd_fast)
        self.macd_slow_ema = bt.indicators.EMA(self.data.close, period=self.p.macd_slow)
        self.macd_signal_ema = bt.indicators.EMA(self.macd_fast_sma - self.macd_slow_ema, period=self.p.macd_signal)
        
        # MACD line as difference between fast SMA and slow EMA
        self.macd = self.macd_fast_sma - self.macd_slow_ema
        
        # Crossover signal
        self.macd_crossover = bt.indicators.CrossOver(self.macd, self.macd_signal_ema)
        
        # Donchian Channel Lower Band
        self.donchian_low = bt.indicators.Lowest(self.data.low, period=self.p.donchian_period)
        self.donchian_high = bt.indicators.Highest(self.data.high, period=self.p.donchian_period)
        #self.donchian_cross = bt.indicators.CrossOver(self.data., self.donchian_low)
        # Trade management variables
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.take_price = None

    def next(self):
        if self.order:
            return  # Wait for pending order execution
        
        # Long entry condition
        if not self.position:
            if self._buy_signal():
                self._enter_long()
        
        # Exit conditions for long position
        else:
            if self.data.close[0] <= self.stop_price or self.data.close[0] >= self.donchian_high[0]:
                self._close_position()

    def _buy_signal(self):
        return (self.data.close[0] > self.ema200[0] and 
                self.macd_crossover[0] > 0)

    def _enter_long(self):
        # Calculate position size using 100% equity
        total_equity = self.broker.getvalue() * 0.9
        self.entry_price = self.data.close[0]
        self.stop_price = self.donchian_low[0]
        risk = self.entry_price - self.donchian_low[0]
        self.take_price = self.entry_price + (risk*2)
        size = total_equity / self.entry_price
        self.order = self.buy(size=size)
        self.log(f'LONG ENTRY: {size:.2f} shares @ {self.entry_price:.2f}')


    def _close_position(self):
        self.order = self.close()
        self.log(f'EXIT: {self.position.size:.2f} shares @ {self.data.close[0]:.2f}')
        self._reset_trade_vars()

    def _reset_trade_vars(self):
        self.entry_price = None
        self.stop_price = None
        self.take_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.size:.2f} @ {order.executed.price:.2f}')
            elif order.issell():
                pnl = order.executed.pnl
                self.log(f'SELL EXECUTED: {order.executed.size:.2f} @ {order.executed.price:.2f} | PnL: ${pnl:.2f}')
            self.order = None

    def log(self, txt):
        dt = self.datas[0].datetime.date(0).isoformat()
        print(f'{dt}: {txt}')


