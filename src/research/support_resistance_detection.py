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

    # Detect pivot points
    def pivotid(df, l, n1, n2):  # n1 and n2 before and after candle l
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

    # Keep n1 and n2 at 10 as per your request
    df['pivot'] = df.apply(lambda x: pivotid(df, df.index.get_loc(x.name), 5, 5), axis=1)

    # Determine point positions for plotting
    def pointpos(x):
        if x['pivot'] == 1:
            return x['low'] - (df['low'].max() * 0.001)
        elif x['pivot'] == 2:
            return x['high'] + (df['high'].max() * 0.001)
        else:
            return np.nan

    df['pointpos'] = df.apply(lambda row: pointpos(row), axis=1)

    # Extract pivot points
    pivot_points = df[df['pivot'] > 0].copy()

    # Get the price for each pivot point
    def get_pivot_price(row):
        if row['pivot'] == 1:
            return row['low']
        elif row['pivot'] == 2:
            return row['high']
        else:
            return np.nan

    pivot_points['price'] = pivot_points.apply(get_pivot_price, axis=1)

    # Function to group pivot points within 5% price range
    def group_pivot_points(pivot_points, max_gap=0.05):
        """
        Group pivot points that are within max_gap (percentage) of each other's price.
        Returns a list of groups, each group is a DataFrame of pivot points.
        """
        # Sort the pivot points by price
        pivot_points = pivot_points.sort_values(by='price')
        pivot_points = pivot_points.reset_index(drop=True)

        groups = []
        current_group = []
        group_prices = []

        for idx, row in pivot_points.iterrows():
            price = row['price']
            if not current_group:
                current_group.append(row)
                group_prices.append(price)
            else:
                # Compare price with the prices in the current group
                if any(abs(price - gp) / gp <= max_gap for gp in group_prices):
                    current_group.append(row)
                    group_prices.append(price)
                else:
                    groups.append(pd.DataFrame(current_group))
                    current_group = [row]
                    group_prices = [price]

        # Add the last group
        if current_group:
            groups.append(pd.DataFrame(current_group))

        return groups

    max_gap = 0.05  # 5%

    # Separate high pivots and low pivots
    high_pivots_grouping = pivot_points[pivot_points['pivot'] == 2]
    low_pivots_grouping = pivot_points[pivot_points['pivot'] == 1]

    # Group the pivot points
    high_groups = group_pivot_points(high_pivots_grouping, max_gap=max_gap)
    low_groups = group_pivot_points(low_pivots_grouping, max_gap=max_gap)

    # Prepare shapes for Plotly
    shapes = []

    # Get the x-axis range
    dfpl = df.copy()  # Plot all data fetched
    x0 = dfpl['date'].min()
    x1 = dfpl['date'].max()

    # For high pivot groups (resistance zones)
    for group in high_groups:
        prices = group['price'].values
        min_price = min(prices)
        max_price = max(prices)
        mean_price = np.mean(prices)

        # Ensure height <=5% of mean price
        height = max_price - min_price
        max_height = mean_price * 0.05  # 5% of mean price

        if len(group) == 1:
            # Single pivot point, draw a line instead of a rectangle
            shape = {
                'type': 'line',
                'xref': 'x',
                'yref': 'y',
                'x0': x0,
                'y0': mean_price,
                'x1': x1,
                'y1': mean_price,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dashdot',
                },
                'layer': 'below',
            }
        else:
            if height > max_height:
                # Adjust min_price and max_price to have height of 5%
                mid_price = (min_price + max_price) / 2
                min_price = mid_price - max_height / 2
                max_price = mid_price + max_height / 2

            # Create the rectangle shape
            shape = {
                'type': 'rect',
                'xref': 'x',
                'yref': 'y',
                'x0': x0,
                'y0': min_price,
                'x1': x1,
                'y1': max_price,
                'line': {
                    'color': 'rgba(255, 0, 0, 0)',  # transparent line
                },
                'fillcolor': 'rgba(255, 0, 0, 0.2)',  # red color with transparency
                'layer': 'below',  # draw below traces
            }
        shapes.append(shape)

    # For low pivot groups (support zones)
    for group in low_groups:
        prices = group['price'].values
        min_price = min(prices)
        max_price = max(prices)
        mean_price = np.mean(prices)

        # Ensure height <=5% of mean price
        height = max_price - min_price
        max_height = mean_price * 0.05  # 5% of mean price

        if len(group) == 1:
            # Single pivot point, draw a line instead of a rectangle
            shape = {
                'type': 'line',
                'xref': 'x',
                'yref': 'y',
                'x0': x0,
                'y0': mean_price,
                'x1': x1,
                'y1': mean_price,
                'line': {
                    'color': 'green',
                    'width': 2,
                    'dash': 'dashdot',
                },
                'layer': 'below',
            }
        else:
            if height > max_height:
                # Adjust min_price and max_price to have height of 5%
                mid_price = (min_price + max_price) / 2
                min_price = mid_price - max_height / 2
                max_price = mid_price + max_height / 2

            # Create the rectangle shape
            shape = {
                'type': 'rect',
                'xref': 'x',
                'yref': 'y',
                'x0': x0,
                'y0': min_price,
                'x1': x1,
                'y1': max_price,
                'line': {
                    'color': 'rgba(0, 255, 0, 0)',  # transparent line
                },
                'fillcolor': 'rgba(0, 255, 0, 0.2)',  # green color with transparency
                'layer': 'below',
            }
        shapes.append(shape)

    # Plot the data
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
        x=pivot_points['date'],
        y=pivot_points['price'],
        mode='markers',
        marker=dict(size=5, color='blue'),
        name='Pivot Points'
    ))

    # Add horizontal lines at pivot points
    for idx, row in pivot_points.iterrows():
        fig.add_hline(y=row['price'], line_dash="dot", line_color="blue",
                      annotation_text=f"<---", annotation_position="right")

    # Get min and max prices for y-axis range
    y_min = min(dfpl['low'].min(), pivot_points['price'].min())
    y_max = max(dfpl['high'].max(), pivot_points['price'].max())

    # Update layout with shapes and y-axis range
    fig.update_layout(
        title=f'Support and Resistance Zones for {symbol}',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(range=[y_min * 0.95, y_max * 1.05], showgrid=False),
        paper_bgcolor='white',
        plot_bgcolor='white',
        shapes=shapes
    )

    # Instead of fig.show(), return the JSON data
    fig_json = json.loads(pio.to_json(fig))
    return fig_json

# Remove or comment out the following lines:
# if __name__ == "__main__":
#     detect_and_plot_support_resistance("BLS", "india")