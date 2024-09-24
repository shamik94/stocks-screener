# src/service/vcp_service.py

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from src.database.models import StockData, VCPStock, ScreenedStock
from datetime import date 

# Turn off SettingWithCopyWarning
pd.options.mode.chained_assignment = None

def run_vcp_detection(db: Session, countries: list):
    # Fetch symbols and countries from the screened_stocks table for the specified countries
    screened_stocks = db.query(ScreenedStock.symbol, ScreenedStock.country).filter(ScreenedStock.country.in_(countries)).all()
    screened_symbols = [s.symbol for s in screened_stocks]
    symbol_country_map = {s.symbol: s.country for s in screened_stocks}

    # Keep track of symbols that meet the VCP criteria
    symbols_meeting_vcp = set()

    for symbol in screened_symbols:
        print("Running VCP detection for Symbol " + symbol)
        # Fetch historical data for the symbol
        stock_entries = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.date).all()

        if len(stock_entries) < 100:
            # Need at least 100 data points for analysis
            continue

        # Prepare DataFrame
        data = pd.DataFrame([{
            'date': entry.date,
            'close': entry.close,
            'high': entry.high,
            'low': entry.low,
            'volume': entry.volume
        } for entry in stock_entries])

        data.set_index('date', inplace=True)

        # Detect VCP pattern
        is_vcp, stage = analyze_vcp(data)

        if is_vcp:
            print("VCP Detected for Symbol " + symbol)
            symbols_meeting_vcp.add(symbol)

            # Check if the stock is already in vcp_stocks
            exists = db.query(VCPStock).filter(VCPStock.symbol == symbol).first()
            if exists:
                # Update the stage if necessary
                if exists.stage != stage:
                    exists.stage = stage
                    db.commit()
            else:
                # Add new VCP stock
                vcp_stock = VCPStock(symbol=symbol, stage=stage, country=symbol_country_map[symbol], detected_date=date.today())
                db.add(vcp_stock)
                db.commit()

    # Remove stocks that no longer meet the VCP criteria for the specified countries
    existing_vcp_stocks = db.query(VCPStock).filter(VCPStock.country.in_(countries)).all()
    for stock in existing_vcp_stocks:
        if stock.symbol not in symbols_meeting_vcp:
            db.delete(stock)
    db.commit()

def analyze_vcp(data, lookback_days=14, contraction_threshold=0.08):
    # Ensure data is sorted by date
    data = data.sort_index()

    # Check if we have enough data
    if len(data) < lookback_days * 2:
        return False, None

    # Split data into recent and prior periods
    recent_data = data.iloc[-lookback_days:]
    prior_data = data.iloc[-(lookback_days * 2):-lookback_days].copy()

    # Calculate ATR for recent data
    recent_data['H-L'] = recent_data['high'] - recent_data['low']
    recent_data['H-PC'] = abs(recent_data['high'] - recent_data['close'].shift(1))
    recent_data['L-PC'] = abs(recent_data['low'] - recent_data['close'].shift(1))
    recent_data['TR'] = recent_data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    recent_atr = recent_data['TR'].mean()

    # Calculate ATR for prior data
    prior_data.loc[:, 'H-L'] = prior_data['high'] - prior_data['low']
    prior_data.loc[:, 'H-PC'] = abs(prior_data['high'] - prior_data['close'].shift(1))
    prior_data.loc[:, 'L-PC'] = abs(prior_data['low'] - prior_data['close'].shift(1))
    prior_data.loc[:, 'TR'] = prior_data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    prior_atr = prior_data['TR'].mean()

    # Avoid division by zero
    if prior_atr == 0:
        return False, None

    # Calculate volatility contraction
    contraction = (prior_atr - recent_atr) / prior_atr

    # Check if contraction meets the threshold
    if contraction < contraction_threshold:
        return False, None

    # Calculate SMAs up to the most recent date
    data['50_SMA'] = data['close'].rolling(window=50).mean()
    data['200_SMA'] = data['close'].rolling(window=200).mean()

    # Get the latest values
    last_close = data['close'].iloc[-1]
    last_50_sma = data['50_SMA'].iloc[-1]
    last_200_sma = data['200_SMA'].iloc[-1]

    # Ensure SMAs are available
    if pd.isna(last_50_sma) or pd.isna(last_200_sma):
        return False, None

    # Check for Stage 2 VCP
    if last_close > last_50_sma > last_200_sma:
        stage = 'Stage 2'
        return True, stage
    else:
        return False, None
