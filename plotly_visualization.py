from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd

def create_backtest_dashboard(trades_df, df, metrics, symbol=''):

    # Ensure required columns exist
    #price_path = f"{price_dir}/{symbol}_1D_indicators.csv"
    #df = pd.read_csv(price_path, index_col=0, parse_dates=True)
    print(metrics)

    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
    required_cols = ['exit_time', 'equity_pct', 'drawdown_pct', 'return_pct']
    missing = [col for col in required_cols if col not in trades_df]
    if missing:
        raise ValueError(f"Missing columns in trades_df: {missing}")

    

    # Create subplots with custom layout
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"type": "indicator", "colspan": 1}, {"type": "indicator", "colspan": 1}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "histogram"}, {"type": "indicator"}],
            [{"type": "candlestick", "colspan": 2}, None]
        ],
        subplot_titles=(
            "Key Metrics", 
            "Equity Curve", 
            "Drawdown",
            "Return Distribution", 
            "Risk/Reward Profile",
            f"{symbol} Price with Trades"
        ),
        vertical_spacing=0.09,
        horizontal_spacing=0.12
    )

    # 1. Top Metrics Indicators -------------------------------------------------
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=metrics['annualized_return_pct'],
        number={'suffix': "%", 'font': {'color': 'green'}},
        title={'text': "Annualized Return"},
        domain={'row': 1, 'column': 1}
    ), row=1, col=1)

    fig.add_trace(go.Indicator(
        mode="number",
        value=metrics['max_drawdown_pct'],
        number={'suffix': "%", 'font': {'color': 'red'}},
        title={'text': "Max Drawdown"},
        domain={'row': 1, 'column': 1}
    ), row=1, col=2)

    # 2. Equity Curve & Drawdown -------------------------------------------------
    fig.add_trace(go.Scatter(
        x=trades_df['exit_time'],
        y=trades_df['equity_pct'],
        mode='lines',
        name='Equity',
        line=dict(color='#2c91de')
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=trades_df['exit_time'],
        y=trades_df['drawdown_pct'],
        mode='lines',
        name='Drawdown',
        line=dict(color='#ff4b4b')
    ), row=2, col=2)

    # 3. Return Distribution & Risk Indicators ------------------------------------
    fig.add_trace(go.Histogram(
        x=trades_df['return_pct'],
        nbinsx=50,
        marker_color='#636efa',
        name='Returns'
    ), row=3, col=1)

    risk_reward_fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number",
        value=metrics['sharpe_ratio'],
        title={'text': "Sharpe Ratio"},
        number={'valueformat': ".2f"},
        domain={'row': 3, 'column': 2}
    ), row=3, col=2)

    # 4. Price Chart with Trades -------------------------------------------------
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
    ), row=4, col=1)

    aapl_trades = trades_df[trades_df['symbol'] == symbol]
    for _, trade in aapl_trades.iterrows():
        fig.add_trace(go.Scatter(
            x=[trade['entry_time']],
            y=[trade['entry_price']],
            mode='markers',
            marker=dict(color='#00cc96', size=10, symbol='triangle-up'),
            showlegend=False
        ), row=4, col=1)

        fig.add_trace(go.Scatter(
            x=[trade['exit_time']],
            y=[trade['exit_price']],
            mode='markers',
            marker=dict(color='#ef553b', size=10, symbol='triangle-down'),
            showlegend=False
        ), row=4, col=1)

    # Layout Configuration -------------------------------------------------------
    fig.update_layout(
        height=1200,
        template="plotly_white",
        title_text="Backtest Performance Dashboard for " + symbol,
        title_x=0.5,
        margin=dict(t=200),
        annotations=[
            dict(text=f"Total Trades: {metrics['total_trades']} | "
                     f"Profit Factor: {metrics['profit_factor']:.2f} | "
                     f"Avg Duration: {metrics['avg_trade_duration_hours']:.1f}h |"
                     f"Avg Trade Value: {metrics['average_trade_value']:.2f}",
                 x=0.5, y=1.05, xref="paper", yref="paper", 
                 showarrow=False, font_size=14)
        ]
    )

    # Axis Labels
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Equity ($)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=2)
    fig.update_yaxes(title_text="Drawdown (%)", row=2, col=2)
    fig.update_xaxes(title_text="Return (%)", row=3, col=1)
    fig.update_yaxes(title_text="Count", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=4, col=1)
    fig.update_yaxes(title_text="Price ($)", row=4, col=1)

    return fig
