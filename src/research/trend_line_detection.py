import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import argparse
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import StockData

# Replace 'your_database_url' with your actual database URL or ensure DATABASE_URL is set in your environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def detect_and_plot_support_resistance(symbol, country):
    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch data from the database
    query = session.query(StockData).filter(
        StockData.symbol == symbol,
        StockData.country == country
    ).order_by(StockData.date)

    df = pd.read_sql(query.statement, session.bind)

    # Ensure 'date' is a datetime object
    df['date'] = pd.to_datetime(df['date'])

    # Optionally, drop duplicates if necessary
    df = df.drop_duplicates()

    # Ensure there are no missing values
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

    # Detect pivot points
    def pivotid(df, l, n1, n2):  # n1 n2 before and after candle l
        if not isinstance(l, int):
            raise ValueError("l must be an integer, not a slice")
        
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

    df['pivot'] = df.apply(lambda x: pivotid(df, df.index.get_loc(x.name), 10, 10), axis=1)

    # Determine point positions for plotting
    def pointpos(x):
        if x['pivot'] == 1:
            return x['low'] - (df['low'].max() * 0.001)
        elif x['pivot'] == 2:
            return x['high'] + (df['high'].max() * 0.001)
        else:
            return np.nan

    df['pointpos'] = df.apply(lambda row: pointpos(row), axis=1)

    # Identify the two most recent pivot points from local highs
    high_pivots = df[df['pivot'] == 2].sort_values(by='date', ascending=False).head(2)
    # Identify the two most recent pivot points from local lows
    low_pivots = df[df['pivot'] == 1].sort_values(by='date', ascending=False).head(2)

    # Prepare data for plotting the high pivot line
    if len(high_pivots) >= 2:
        x_high = [high_pivots['date'].iloc[1], high_pivots['date'].iloc[0]]
        y_high = [high_pivots['high'].iloc[1], high_pivots['high'].iloc[0]]
    else:
        x_high = []
        y_high = []

    # Prepare data for plotting the low pivot line
    if len(low_pivots) >= 2:
        x_low = [low_pivots['date'].iloc[1], low_pivots['date'].iloc[0]]
        y_low = [low_pivots['low'].iloc[1], low_pivots['low'].iloc[0]]
    else:
        x_low = []
        y_low = []

    # Plot the data
    dfpl = df[df['date'] >= (df['date'].max() - pd.Timedelta(days=300))]  # Adjust the range as needed
    fig = go.Figure(data=[go.Candlestick(
        x=dfpl['date'],
        open=dfpl['open'],
        high=dfpl['high'],
        low=dfpl['low'],
        close=dfpl['close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='OHLC'
    )])

    # Add pivot points to the plot
    fig.add_trace(go.Scatter(
        x=dfpl['date'],
        y=dfpl['pointpos'],
        mode='markers',
        marker=dict(size=5, color='blue'),
        name='Pivot Points'
    ))

    # Add the high pivot line to the plot
    if len(x_high) == 2:
        fig.add_trace(go.Scatter(
            x=x_high,
            y=y_high,
            mode='lines',
            line=dict(color='magenta', width=2),
            name='High Trend Line'
        ))

    # Add the low pivot line to the plot
    if len(x_low) == 2:
        fig.add_trace(go.Scatter(
            x=x_low,
            y=y_low,
            mode='lines',
            line=dict(color='cyan', width=2),
            name='Low Trend Line'
        ))

    # Update layout
    fig.update_layout(
        title=f'Support and Resistance Lines for {symbol}',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    fig.show()

    session.close()

# Take symbol and country as input
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Detect and plot support and resistance levels.')
    parser.add_argument('symbol', type=str, help='Stock symbol')
    parser.add_argument('country', type=str, help='Country')
    args = parser.parse_args()
    detect_and_plot_support_resistance(args.symbol, args.country)
