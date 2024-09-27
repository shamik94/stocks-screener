import sys
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import StockData
from src.research.breakout_signals import generate_buy_signal
# Replace 'your_database_url' with your actual database URL or ensure DATABASE_URL is set in your environment
DATABASE_URL = os.environ.get('DATABASE_URL')
last_n_months = 6  # Number of months to fetch data

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

def generate_buy_signal_random(df):
    short_window=20
    long_window=50
    idx = df.index[-1]  # Define idx as the last index of the DataFrame
    df = df.iloc[:idx+1]
    short_sma = df['close'].rolling(window=short_window, min_periods=1).mean().iloc[-1]
    long_sma = df['close'].rolling(window=long_window, min_periods=1).mean().iloc[-1]
    return short_sma > long_sma

def backtest_strategy(df, profit_target=0.06, stop_loss=-0.03, initial_cash=10000.0):
    in_position = False
    entry_price = 0
    entry_date = None
    cash = initial_cash
    position = 0
    trades = []
    portfolio_values = []

    for idx, row in df.iterrows():
        date = row['date']
        price = row['close']

        if not in_position:
            if generate_buy_signal(df, price):
                shares_to_buy = cash // price
                if shares_to_buy > 0:
                    entry_price = price
                    entry_date = date
                    in_position = True
                    position = shares_to_buy
                    cash -= position * price
                    print(f"Bought {position} shares at {entry_price} on {entry_date}")
        else:
            pl_pct = (price - entry_price) / entry_price
            if pl_pct >= profit_target or pl_pct <= stop_loss:
                if pl_pct >= profit_target:
                    exit_price = entry_price * (1 + profit_target)
                elif pl_pct <= stop_loss:
                    exit_price = entry_price * (1 + stop_loss)
                
                exit_date = date
                cash += position * exit_price
                holding_period = (exit_date - entry_date).days
                trade = {
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pl_pct': (exit_price - entry_price) / entry_price,
                    'holding_period': holding_period
                }
                trades.append(trade)
                print(f"Sold {position} shares at {exit_price} on {exit_date} with P/L of {trade['pl_pct']:.2%}")
                in_position = False
                position = 0
                entry_price = 0
                entry_date = None

        portfolio_value = cash + position * price if in_position else cash
        portfolio_values.append({'date': date, 'portfolio_value': portfolio_value})

    return trades, portfolio_values

def calculate_metrics(portfolio_values, trades):
    portfolio_df = pd.DataFrame(portfolio_values)
    portfolio_df['daily_return'] = portfolio_df['portfolio_value'].pct_change()
    portfolio_df.dropna(inplace=True)

    mean_return = portfolio_df['daily_return'].mean()
    if mean_return == 0:
        return 0, 0, 0, pd.DataFrame()
    std_return = portfolio_df['daily_return'].std()
    sharpe_ratio = (mean_return / std_return) * np.sqrt(252)

    trades_df = pd.DataFrame(trades)
    average_pl = trades_df['pl_pct'].mean()
    
    # Debugging: Print the columns of trades_df
    print("Columns in trades_df:", trades_df.columns)
    
    # Debugging: Print the first few rows of trades_df
    print("First few rows of trades_df:\n", trades_df.head())
    
    # Calculate win ratio
    win_ratio = (trades_df['pl_pct'] > 0).mean()

    return sharpe_ratio, average_pl, win_ratio, trades_df

def main():
    session = create_db_session(DATABASE_URL)
    start_date = datetime.now() - timedelta(days=last_n_months * 30)
    df = fetch_stock_data(session, "AAPL", "usa", start_date)
    trades, portfolio_values = backtest_strategy(df)
    sharpe_ratio, average_pl, win_ratio, trades_df = calculate_metrics(portfolio_values, trades)

    print("\n--- Backtesting Results ---")
    print(f"Total Trades Executed: {len(trades)}")
    print(f"Average P/L per Trade: {average_pl:.2%}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Win Ratio: {win_ratio:.2%}")

    print("\nTrade Log:")
    print(trades_df)

if __name__ == "__main__":
    main()
