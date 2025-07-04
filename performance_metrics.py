import numpy as np
#minutes per_bar = 1440 day, 60 1 hour


def calculate_backtest_metrics(trades_df, initial_capital=100000, minutes_per_bar=1440, trading_days=252):
    """Calculate performance metrics and enhance trades DataFrame"""
    # Calculate equity first
    trades_df['equity'] = initial_capital + trades_df['pnlcomm'].cumsum()
    trades_df['equity_pct'] = ((initial_capital + trades_df['pnlcomm'].cumsum()) / initial_capital) * 100


    # Calculate drawdown
    trades_df['roll_max_pct'] = trades_df['equity_pct'].cummax()
    trades_df['drawdown_pct'] = (trades_df['equity_pct'] - trades_df['roll_max_pct']) 

    #trades_df['roll_max'] = trades_df['equity'].cummax()
    #trades_df['drawdown'] = trades_df['equity'] - trades_df['roll_max']
    trades_df['return_pct'] = (trades_df['pnlcomm'] / initial_capital) * 100
    trades_df['duration_hours'] = trades_df['duration'] * minutes_per_bar / 60


    closed_trades = trades_df[trades_df['status'] == 'closed'].copy()
    
    if len(closed_trades) == 0:
        return {"Error": "No closed trades to analyze"}
    
    # Calculate derivatives
    closed_trades['return_pct'] = (closed_trades['pnlcomm'] / initial_capital) * 100
    closed_trades['duration_hours'] = closed_trades['duration'] * minutes_per_bar / 60
    
    # Create equity curve with datetime index
    closed_trades['equity'] = initial_capital + closed_trades['pnlcomm'].cumsum()
    equity_curve = closed_trades.set_index('exit_time')['equity'].resample('D').last().ffill().to_frame()
    
    # For closed trades only
    closed_trades = trades_df[trades_df['status'] == 'closed'].copy()
    closed_trades['equity_pct'] = ((initial_capital + closed_trades['pnlcomm'].cumsum()) / initial_capital) * 100
    closed_trades['roll_max_pct'] = closed_trades['equity_pct'].cummax()
    closed_trades['drawdown_pct'] = round(closed_trades['equity_pct'] - closed_trades['roll_max_pct'], 2)


    metrics = {
        'total_trades': len(closed_trades),
        'win_rate': (closed_trades['pnlcomm'] > 0).mean() * 100,
        'profit_factor': (closed_trades[closed_trades['pnlcomm'] > 0]['pnlcomm'].sum() /
                        abs(closed_trades[closed_trades['pnlcomm'] < 0]['pnlcomm'].sum())),
        'avg_trade_duration_hours': closed_trades['duration_hours'].mean(),
        'max_drawdown_pct': calculate_max_drawdown(equity_curve['equity']),
        'sharpe_ratio': calculate_sharpe(closed_trades['return_pct'], minutes_per_bar, trading_days),
        'annualized_return_pct': calculate_annualized_return(equity_curve, initial_capital, trading_days),
        'total_return_pct': (closed_trades['pnlcomm'].sum() / initial_capital) * 100,
        'average_trade_value': calculate_average_trade_value(closed_trades),
        'max_drawdown_pct': closed_trades['drawdown_pct'].min(),
        'peak_equity_pct': closed_trades['roll_max_pct'].max(),
        'final_equity_pct': closed_trades['equity_pct'].iloc[-1]
    }
    
    return metrics

def calculate_max_drawdown(equity_series):
    """Calculate maximum drawdown from equity series"""
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    return drawdown.min() * 100  # Return as percentage

def calculate_sharpe(returns, minutes_per_bar, trading_days):
    """Annualized Sharpe Ratio calculation"""
    if returns.std() == 0:
        return 0.0
    bars_per_year = (trading_days * 6.5 * 60) / minutes_per_bar
    return (returns.mean() / returns.std()) * np.sqrt(bars_per_year)

def calculate_annualized_return(equity_df, initial_capital, trading_days):
    """Calculate annualized return percentage"""
    start_date = equity_df.index.min()
    end_date = equity_df.index.max()
    days_active = max((end_date - start_date).days, 1)
    total_return = equity_df['equity'].iloc[-1] / initial_capital - 1
    return round(((1 + total_return) ** (trading_days / days_active) - 1) * 100, 2)

def calculate_average_trade_value(closed_trades):
    # Calculate average trade size
    average_value = closed_trades['size'] * closed_trades['entry_price']
    
    return average_value.mean()
