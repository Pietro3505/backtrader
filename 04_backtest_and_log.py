import backtrader as bt
import pandas as pd
import os
import strategy_logic
from performance_metrics import calculate_backtest_metrics
from plotly_visualization import create_backtest_dashboard
from export_to_excel import export_trades_and_dashboard_to_excel
from calculate_indicators import params

# einstieg macd donchian

class TradeLogger(bt.Analyzer):
    def __init__(self):
        self.trades = []
        self.trade_ids = set()
        
    def notify_trade(self, trade):
        current_dt = self._convert_datetime(trade.data, trade.data.datetime[0])
        trade_id = trade.ref or id(trade)
        
        if trade_id not in self.trade_ids:
            self._create_trade(trade, trade_id, current_dt)
            self.trade_ids.add(trade_id)
        else:
            self._update_trade(trade, trade_id, current_dt)

    def _create_trade(self, trade, trade_id, dt):
        self.trades.append({
            'trade_id': trade_id,
            'symbol': trade.data._name,
            'entry_time': dt,
            'exit_time': pd.NaT,
            'entry_price': trade.price,
            'exit_price': None,
            'size': trade.size,
            'status': 'open',
            'pnl': 0,
            'pnlcomm': 0,
            'duration': 0  # Initialize duration
        })

    def _update_trade(self, trade, trade_id, dt):
        for t in reversed(self.trades):
            if t['trade_id'] == trade_id:
                # Update exit information
                is_closed = trade.isclosed
                t.update({
                    'exit_time': self._convert_datetime(trade.data, trade.dtclose) if is_closed else dt,
                    'exit_price': trade.price if is_closed else None,
                    'status': 'closed' if is_closed else 'open',
                    'pnl': trade.pnl,
                    'pnlcomm': trade.pnlcomm
                })
                
                # Calculate duration when trade closes
                if is_closed:
                    entry = t['entry_time']
                    exit = t['exit_time']
                    if pd.notnull(entry) and pd.notnull(exit):
                        t['duration'] = (exit - entry).total_seconds() / (3600 * 24) #in days
                    else:
                        t['duration'] = 0
                break

    def _convert_datetime(self, data, dt):
        try:
            return data.num2date(int(dt)).replace(tzinfo=None)
        except:
            return pd.NaT

    def get_analysis(self):
        return pd.DataFrame(self.trades)
    



# Run backtest for each stock

# Load preprocessed indicator data
data_dir = "data"
data = {}
for file in os.listdir(data_dir):
    if file.endswith("_1D_indicators.csv"):
        symbol = file.split("_")[0]
        df = pd.read_csv(os.path.join(data_dir, file), index_col=0, parse_dates=True)
        # Fix column names and filter
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })[['open', 'high', 'low', 'close', 'volume']]  # Keep only essential columns
        data[symbol] = df

results = []
number_of_stocks = len(data)
number_of_errors = 0
for symbol, df in data.items():
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.set_shortcash(False)  # Required for proper trade history
    cerebro.broker.setcommission(commission=0.001)  
    cerebro.broker.set_eosbar(False)  # Don't close trades at end of day
    cerebro.broker.set_coo(True)  # Enable Cheat-On-Open for better execution prices
    cerebro.broker.set_coc(True)


    # Add closing timer
    cerebro.add_timer(
        when=bt.Timer.SESSION_END,
        timername='force_close',
        monthdays=[1],  # Force close on 1st of each month
        callback=lambda self: self.close() if self.position else None
    )


    data_feed = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # Use index as datetime
        open=0,  # Adjust column indices based on your CSV structure
        high=1,
        low=2,
        close=3,
        volume=4,
        openinterest=-1
    )
    data_feed._name = symbol  # Sets data name for tracking
    cerebro.adddata(data_feed)

    # Use params to configure strategy
    cerebro.addstrategy(strategy_logic.EMAMACDStrategy)
    #cerebro.addstrategy(strategy_logic.EMAFILTERCROSS)
    cerebro.addanalyzer(TradeLogger, _name='trade_logger')


    print(f"Running backtest for {symbol}...")
    strat_results = cerebro.run()
    
    trades_df = strat_results[0].analyzers.trade_logger.get_analysis()

    if not trades_df.empty:  # Check if results exist
        trades_df['symbol'] = symbol
        results.append(trades_df)
        metrics = calculate_backtest_metrics(trades_df)
        # Generate dashboard
        dashboard = create_backtest_dashboard(
            trades_df, df,
            metrics,
            symbol=symbol
        )
        # Save dashboard HTML
        if not os.path.exists("backtest_results"):
            os.mkdir("backtest_results") 
        dashboard_html_path = os.path.join("backtest_results", f"backtest_{symbol}.html")
        dashboard.write_html(dashboard_html_path)
        
        dashboard.show()

        # Export trades and dashboard link to Excel
        excel_path = f"./backtest_results/backtest_{symbol}_report.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            trades_df.to_excel(writer, sheet_name='Trades', index=False)
            workbook = writer.book
            worksheet = workbook.add_worksheet('Dashboard')
            # Insert hyperlink to dashboard HTML file
            worksheet.write_url('A1', f'file://{os.path.abspath(dashboard_html_path)}', string='Open Dashboard HTML')

    else:
        print(f"No results for {symbol}")
        number_of_errors += 1

if number_of_errors < number_of_stocks:
    print(f"Backtest completed with {number_of_errors} errors.")
    # Combine all trades into a single DataFrame
    all_trades_df = pd.concat(results, ignore_index=True)
    all_trades_df.to_csv("backtest_trades.csv", index=False)
    print("Backtest complete and trades logged.")

else:
    print("All backtests failed. Please check your data and strategy.")









