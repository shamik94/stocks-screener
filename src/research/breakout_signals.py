import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import StockData

# Constants
DATABASE_URL = os.environ.get('DATABASE_URL')
REQUIRED_MONTHS = 6
SYMBOL = "GRAVITA"
COUNTRY = "india"
PIVOT_WINDOW = 10
PROFIT_TARGET_PERCENTAGE = 0.10
MAX_STOP_LOSS_PERCENTAGE = 0.08
BREAKOUT_THRESHOLD = 1.06
PLOT_DAYS_AFTER_SIGNAL = 30
LAST_N_RESISTANCE_LEVELS = 1

def create_db_session(database_url):
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def fetch_stock_data(session, symbol, country, start_date=None, end_date=None):
    query = session.query(StockData).filter(
        StockData.symbol == symbol,
        StockData.country == country
    )
    
    if start_date is not None:
        query = query.filter(StockData.date >= start_date)
    
    if end_date is not None:
        query = query.filter(StockData.date <= end_date)
    
    query = query.order_by(StockData.date)
    
    df = pd.read_sql(query.statement, session.bind)
    df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates()
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
    return df.sort_values('date').reset_index(drop=True)

def generate_buy_signal(df, open_price, close_price):
    def pivotid(df, l, n1, n2):
        if l - n1 < 0 or l + n2 >= len(df):
            return 0

        pividlow = 1
        pividhigh = 1
        for i in range(l - n1, l + n2 + 1):
            if df['low'].iloc[l] > df['low'].iloc[i]:
                pividlow = 0
            if df['high'].iloc[l] < df['high'].iloc[i]:
                pividhigh = 0
        if pividlow and pividhigh:
            return 3
        elif pividlow:
            return 1
        elif pividhigh:
            return 2
        else:
            return 0

    df = df.copy()
    df.reset_index(drop=True, inplace=True)

    # Compute pivots
    df['pivot'] = [pivotid(df, idx, PIVOT_WINDOW, PIVOT_WINDOW) for idx in range(len(df))]

    # Extract high pivots (resistance levels)
    high_pivots = df[df['pivot'] == 2].copy()
    high_pivots['price'] = high_pivots['high']

    # Sort high pivots by date descending to get recent ones first
    high_pivots = high_pivots.sort_values(by='date', ascending=False)

    # Get the last N resistance levels
    recent_high_pivots = high_pivots.head(LAST_N_RESISTANCE_LEVELS)

    # Get resistance levels from recent pivots
    resistance_levels = sorted(recent_high_pivots['price'].unique())

    if not resistance_levels:
        # No resistance levels found
        return False, None, None

    # Now, check for breakout above any recent resistance level
    # A breakout occurs if open_price < level and close_price > level
    broken_levels = [level for level in resistance_levels if open_price < level < close_price]

    if not broken_levels:
        # No breakout above any recent resistance level
        return False, None, None

    # Process the highest broken level (the largest level that is broken)
    breakout_level = max(broken_levels)

    # Find the levels above the breakout level among recent resistance levels
    levels_above = [lvl for lvl in resistance_levels if lvl > breakout_level]

    # Check if next level is at least 6% away
    next_levels = [lvl for lvl in levels_above if lvl >= breakout_level * BREAKOUT_THRESHOLD]

    if next_levels:
        # Next higher level is at least 6% away
        profit_target = min(next_levels)
    else:
        # No levels at least 6% away; set profit target to 10% above close price
        profit_target = close_price * (1 + PROFIT_TARGET_PERCENTAGE)

    # Calculate profit percentage
    profit_percentage = (profit_target - close_price) / close_price

    # Calculate stop loss percentage: min(profit_percentage / 2, MAX_STOP_LOSS_PERCENTAGE)
    stop_loss_percentage = min(profit_percentage / 2, MAX_STOP_LOSS_PERCENTAGE)

    # Calculate stop loss price
    stop_loss_price = close_price * (1 - stop_loss_percentage)

    # Ensure stop loss is not below any significant support level
    # (Optional: You can compare with previous support levels if needed)

    # Generate buy signal
    return True, stop_loss_price, profit_target

def main():
    if DATABASE_URL is None:
        print("Error: DATABASE_URL is not set in the environment variables.")
        return

    session = create_db_session(DATABASE_URL)

    # Fetch all available data
    df_all = fetch_stock_data(session, SYMBOL, COUNTRY)
    if df_all.empty:
        print("No data available for the given symbol and country.")
        return

    # Filter out weekends from df_all
    df_all = df_all[df_all['date'].dt.dayofweek < 5].reset_index(drop=True)

    # Initialize lists to store buy signals
    buy_dates = []
    buy_prices = []
    stop_losses = []
    profit_targets = []

    # Loop through each date starting from the date where we have at least REQUIRED_MONTHS of data
    min_date = df_all['date'].min() + pd.DateOffset(months=REQUIRED_MONTHS)
    max_date = df_all['date'].max()

    date_range = df_all[(df_all['date'] >= min_date) & (df_all['date'] <= max_date)]['date'].unique()

    for prediction_date in date_range:
        prediction_date = pd.to_datetime(prediction_date)

        # Calculate start date (at least REQUIRED_MONTHS before prediction date)
        start_date = prediction_date - pd.DateOffset(months=REQUIRED_MONTHS)
        end_date = prediction_date  # Include data up to prediction_date

        df = df_all[(df_all['date'] >= start_date) & (df_all['date'] <= end_date)].copy()

        if df.empty or df['date'].max() < prediction_date:
            continue  # Not enough data for this date

        # Check if we have at least REQUIRED_MONTHS of data
        data_duration = df['date'].max() - df['date'].min()
        if data_duration < pd.Timedelta(days=REQUIRED_MONTHS * 30):
            continue  # Not enough data

        # Get open and close price on prediction date
        prediction_day_data = df[df['date'] == prediction_date]
        if prediction_day_data.empty:
            continue  # No data for prediction date

        open_price = prediction_day_data['open'].iloc[0]
        close_price = prediction_day_data['close'].iloc[0]

        # Generate buy signal
        signal, stop_loss, profit_target = generate_buy_signal(df, open_price, close_price)

        if signal:
            buy_dates.append(prediction_date)
            buy_prices.append(close_price)
            stop_losses.append(stop_loss)
            profit_targets.append(profit_target)

    if not buy_dates:
        print("No buy signals generated.")
        return

    # Plotting the price data, volume, and buy signals using Plotly
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df_all['date'],
        open=df_all['open'],
        high=df_all['high'],
        low=df_all['low'],
        close=df_all['close'],
        name='Price'
    ), row=1, col=1)

    # Add volume bars
    fig.add_trace(go.Bar(
        x=df_all['date'],
        y=df_all['volume'],
        name='Volume',
        marker_color='rgba(0, 0, 255, 0.5)'
    ), row=2, col=1)

    # Add buy signals
    fig.add_trace(go.Scatter(
        x=buy_dates,
        y=buy_prices,
        mode='markers',
        name='Buy Signal',
        marker=dict(symbol='triangle-up', color='green', size=10)
    ), row=1, col=1)

    # Add stop loss and profit target lines as shapes
    shapes = []

    for idx, buy_date in enumerate(buy_dates):
        # Convert dates to string format for Plotly
        buy_date_str = buy_date.strftime('%Y-%m-%d')
        end_date_str = (buy_date + pd.Timedelta(days=PLOT_DAYS_AFTER_SIGNAL)).strftime('%Y-%m-%d')

        # Stop loss line
        shapes.append(dict(
            type='line',
            xref='x', yref='y',
            x0=buy_date_str, y0=stop_losses[idx],
            x1=end_date_str, y1=stop_losses[idx],
            line=dict(color='red', dash='dash'),
            layer='below'
        ))

        # Profit target line
        shapes.append(dict(
            type='line',
            xref='x', yref='y',
            x0=buy_date_str, y0=profit_targets[idx],
            x1=end_date_str, y1=profit_targets[idx],
            line=dict(color='green', dash='dash'),
            layer='below'
        ))

        # Vertical line from stop loss to profit target at buy date
        shapes.append(dict(
            type='line',
            xref='x', yref='y',
            x0=buy_date_str, y0=stop_losses[idx],
            x1=buy_date_str, y1=profit_targets[idx],
            line=dict(color='gray', dash='dot'),
            layer='below'
        ))

    # Update layout with shapes and disable weekends
    fig.update_layout(
        title=f"{SYMBOL} Price Chart with Buy Signals",
        xaxis_title='Date',
        yaxis_title='Price',
        shapes=shapes,
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
            rangebreaks=[dict(bounds=["sat", "mon"])]  # This line disables weekends
        ),
        yaxis=dict(title='Price'),
        yaxis2=dict(title='Volume'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    # Add annotations for Stop Loss and Profit Target
    fig.add_annotation(
        x=0.02, y=0.98, xref='paper', yref='paper',
        text='Red dashed line: Stop Loss<br>Green dashed line: Profit Target',
        showarrow=False,
        font=dict(size=10),
        align='left',
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='black',
        borderwidth=1
    )

    # Show the figure
    fig.show()

if __name__ == "__main__":
    main()
