import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import StockData, VCPStock

DATABASE_URL = os.environ.get('DATABASE_URL')


def detect_and_plot_vcp(symbol='NELCO', country='india'):
    # Create database connection
    engine = create_engine(DATABASE_URL)  # Replace with your actual database URL
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch data from the database
    query = session.query(StockData).filter(
        StockData.symbol == symbol,
        StockData.country == country
    ).order_by(StockData.date)
    
    df = pd.read_sql(query.statement, session.bind)
    df.set_index('date', inplace=True)

    # Calculate technical indicators manually

    # Simple Moving Averages
    df['50_SMA'] = df['close'].rolling(window=50).mean()
    df['200_SMA'] = df['close'].rolling(window=200).mean()

    # True Range (TR) components
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))

    # True Range (TR)
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    # Average True Range (ATR)
    df['ATR'] = df['TR'].rolling(window=14).mean()

    # Volatility Contraction Identification
    df['ATR_Ratio'] = df['ATR'] / df['close']
    df['Contraction'] = df['ATR_Ratio'].rolling(window=10).mean()

    # Identify VCP stages
    df['VCP_Stage'] = np.nan
    lookback = 20
    contraction_threshold = 0.9  # Adjust as needed

    for i in range(lookback, len(df)):
        recent_contractions = df['Contraction'].iloc[i-lookback:i]
        if df['Contraction'].iloc[i] < recent_contractions.mean() * contraction_threshold:
            if df['close'].iloc[i] > df['50_SMA'].iloc[i] > df['200_SMA'].iloc[i]:
                df.loc[df.index[i], 'VCP_Stage'] = 'Stage 2'
            elif df['close'].iloc[i] < df['50_SMA'].iloc[i] < df['200_SMA'].iloc[i]:
                df.loc[df.index[i], 'VCP_Stage'] = 'Stage 4'

    # Plot the stock data and VCP detections
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ))

    # Add SMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['50_SMA'], mode='lines', name='50 SMA', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['200_SMA'], mode='lines', name='200 SMA', line=dict(color='red')))

    # Add VCP detections
    stage_2_vcp = df[df['VCP_Stage'] == 'Stage 2']
    stage_4_vcp = df[df['VCP_Stage'] == 'Stage 4']

    fig.add_trace(go.Scatter(
        x=stage_2_vcp.index, 
        y=stage_2_vcp['high'],
        mode='markers',
        marker=dict(symbol='triangle-up', size=10, color='green'),
        name='Stage 2 VCP'
    ))

    fig.add_trace(go.Scatter(
        x=stage_4_vcp.index, 
        y=stage_4_vcp['low'],
        mode='markers',
        marker=dict(symbol='triangle-down', size=10, color='red'),
        name='Stage 4 VCP'
    ))

    # Update layout
    fig.update_layout(
        title=f'VCP Detection for {symbol}',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )

    fig.show()

    session.close()

# Call the function
detect_and_plot_vcp('NELCO', 'india')
