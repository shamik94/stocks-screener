import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import StockData
import datetime

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
    df.set_index('date', inplace=True)

    # Ensure the index is unique
    df = df.reset_index(drop=True)

    # Optionally, drop duplicates if necessary
    df = df.drop_duplicates()

    # After fetching the data
    print(f"Fetched data shape: {df.shape}")
    print(f"First few rows of data:\n{df.head()}")

    # Ensure there are no missing values
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

    # Before pivot calculation
    print(f"Data types of columns:\n{df.dtypes}")

    # Detect pivot points
    def pivotid(df, l, n1, n2):  # n1 n2 before and after candle l
        print(f"pivotid called with l={l}, n1={n1}, n2={n2}")  # Debug print
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

    # Plot the data
    dfpl = df[-300:]  # You can adjust the range as needed
    fig = go.Figure(data=[go.Candlestick(
        x=dfpl.index,
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
        x=dfpl.index,
        y=dfpl['pointpos'],
        mode='markers',
        marker=dict(size=10, color='Blue'),
        name='Pivot Points'
    ))

    # Update layout
    fig.update_layout(
        title=f'Support and Resistance Levels for {symbol}',
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
    symbol = input("Enter stock symbol: ")
    country = input("Enter country: ")
    detect_and_plot_support_resistance(symbol, country)
