import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import StockData

# Replace 'your_database_url' with your actual database URL or ensure DATABASE_URL is set in your environment
DATABASE_URL = os.environ.get('DATABASE_URL')
last_n_months = 60  # Number of months to fetch data

def create_db_session(database_url):
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def fetch_stock_data(session, symbol, country, start_date):
    query = session.query(StockData).filter(
        StockData.symbol == symbol,
        StockData.country == country,
        StockData.date >= start_date
    ).order_by(StockData.date)
    df = pd.read_sql(query.statement, session.bind)
    df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates()
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
    return df.sort_values('date').reset_index(drop=True)

def generate_buy_signal(df, current_price):
    # Compute pivot points
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

    # Extract high pivots (resistance levels)
    high_pivots = df[df['pivot'] == 2].copy()
    high_pivots['price'] = high_pivots['high']

    # Get resistance levels
    resistance_levels = high_pivots['price'].tolist()

    # Get the two most recent high pivots for trend line
    high_pivots = high_pivots.sort_values(by='date', ascending=False)

    if len(high_pivots) >= 2:
        # Get the two most recent high pivots
        hp1 = high_pivots.iloc[0]
        hp2 = high_pivots.iloc[1]

        # Coordinates for the trend line
        x1 = hp1['date'].toordinal()
        y1 = hp1['price']

        x2 = hp2['date'].toordinal()
        y2 = hp2['price']

        # Compute the slope and intercept
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        # Today's date in numerical format
        x_today = df['date'].iloc[-1].toordinal()
        trendline_price = slope * x_today + intercept
    else:
        trendline_price = None

    # Check if current_price breaks above resistance levels
    breaks_resistance = False
    broken_resistance_level = None
    for level in resistance_levels:
        if current_price > level:
            breaks_resistance = True
            broken_resistance_level = level
            break  # Break after the first resistance level is broken

    # Check if current_price breaks above trendline
    if trendline_price is not None:
        breaks_trendline = current_price > trendline_price
    else:
        breaks_trendline = False

    # Check for convergence (resistance level and trendline are close)
    convergence = False
    if broken_resistance_level is not None and trendline_price is not None:
        if abs(trendline_price - broken_resistance_level) / broken_resistance_level < 0.01:  # within 1%
            convergence = True

    # Determine probability
    if convergence and breaks_resistance and breaks_trendline:
        probability = 'high'
    elif breaks_resistance and breaks_trendline:
        probability = 'medium'
    elif breaks_resistance or breaks_trendline:
        probability = 'low'
    else:
        probability = 'none'

    # Generate buy signal if probability is not 'none'
    if probability != 'none':
        signal = 'buy'
    else:
        signal = 'no signal'
    print(f"Signal: {signal}, Probability: {probability}")
    # Return signal and probability
    return signal == 'buy' and (probability == 'high' or probability == 'medium' or probability == 'low')

def main():
    session = create_db_session(DATABASE_URL)
    start_date = datetime.now() - timedelta(days=last_n_months * 30)
    symbol = "AAPL"  # Replace with your desired symbol
    country = "usa"  # Replace with your desired country
    df = fetch_stock_data(session, symbol, country, start_date)

    # Get current price (assuming the last close price)
    current_price = df['close'].iloc[-1]

    # Generate buy signal
    signal_info = generate_buy_signal(df, current_price)

    print("\n--- Buy Signal ---")
    print(f"Symbol: {symbol}")
    print(f"Current Price: {current_price}")
    print(f"Signal: {signal_info['signal']}")
    print(f"Probability: {signal_info['probability']}")

if __name__ == "__main__":
    main()
