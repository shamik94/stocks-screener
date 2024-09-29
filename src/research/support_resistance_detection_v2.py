import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import plotly.io as pio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import StockData

# Replace 'your_database_url' with your actual database URL or ensure DATABASE_URL is set in your environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def detect_and_plot_support_resistance(symbol, country, months=6):
    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Calculate the date N months ago from today
    start_date = datetime.now() - timedelta(days=months * 30)

    # Fetch data from the database for the last N months
    query = session.query(StockData).filter(
        StockData.symbol == symbol,
        StockData.country == country,
        StockData.date >= start_date
    ).order_by(StockData.date)

    df = pd.read_sql(query.statement, session.bind)

    # Ensure 'date' is a datetime object
    df['date'] = pd.to_datetime(df['date'])

    # Optionally, drop duplicates if necessary
    df = df.drop_duplicates()

    # Ensure there are no missing values
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

    df = df.reset_index(drop=True)  # Reset index to ensure integer indexing

    # Implement support and resistance detection

    def support(df, l, n1, n2):
        if l - n1 < 0 or l + n2 >= len(df):
            return 0
        for i in range(l - n1 + 1, l + 1):
            if df['low'].iloc[i] > df['low'].iloc[i - 1]:
                return 0
        for i in range(l + 1, l + n2 + 1):
            if df['low'].iloc[i] < df['low'].iloc[i - 1]:
                return 0
        return 1

    def resistance(df, l, n1, n2):
        if l - n1 < 0 or l + n2 >= len(df):
            return 0
        for i in range(l - n1 + 1, l + 1):
            if df['high'].iloc[i] < df['high'].iloc[i - 1]:
                return 0
        for i in range(l + 1, l + n2 + 1):
            if df['high'].iloc[i] > df['high'].iloc[i - 1]:
                return 0
        return 1

    sr = []
    n1 = 3
    n2 = 2
    for row in range(n1, len(df) - n2):
        if support(df, row, n1, n2):
            sr.append((row, df['low'].iloc[row], 1))
        if resistance(df, row, n1, n2):
            sr.append((row, df['high'].iloc[row], 2))

    # Collect support and resistance levels
    support_levels = pd.DataFrame([(row, price) for row, price, typ in sr if typ == 1], columns=['index', 'price'])
    resistance_levels = pd.DataFrame([(row, price) for row, price, typ in sr if typ == 2], columns=['index', 'price'])

    # Remove duplicates within a certain percentage
    max_gap_percent = 0.005  # 0.5%

    def get_unique_levels(levels, max_gap_percent):
        unique_levels = []
        levels = sorted(levels)
        last_level = None
        for price in levels:
            if last_level is None:
                unique_levels.append(price)
                last_level = price
            else:
                if abs(price - last_level) / last_level > max_gap_percent:
                    unique_levels.append(price)
                    last_level = price
        return unique_levels

    unique_support_levels = get_unique_levels(support_levels['price'].tolist(), max_gap_percent)
    unique_resistance_levels = get_unique_levels(resistance_levels['price'].tolist(), max_gap_percent)

    # Plot the data
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='OHLC'
    )])

    # Add support levels
    for level in unique_support_levels:
        fig.add_shape(type='line',
            x0=df['date'].min(),
            y0=level,
            x1=df['date'].max(),
            y1=level,
            line=dict(color='green', width=1, dash='dash'),
            name='Support Level'
        )

    # Add resistance levels
    for level in unique_resistance_levels:
        fig.add_shape(type='line',
            x0=df['date'].min(),
            y0=level,
            x1=df['date'].max(),
            y1=level,
            line=dict(color='red', width=1, dash='dash'),
            name='Resistance Level'
        )

    # Update layout
    fig.update_layout(
        title=f'Support and Resistance Zones for {symbol}',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    # Instead of fig.show(), return the JSON data
    fig_json = json.loads(pio.to_json(fig))
    return fig_json

# Remove or comment out the following lines:
# if __name__ == "__main__":
#     detect_and_plot_support_resistance("BLS", "india")