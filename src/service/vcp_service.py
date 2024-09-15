# src/service/vcp_service.py

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from src.database.models import StockData, VCPStock, ScreenedStock

def run_vcp_detection(db: Session):
    # Fetch symbols from the screened_stocks table
    screened_symbols = db.query(ScreenedStock.symbol).all()
    screened_symbols = [s[0] for s in screened_symbols]

    # Keep track of symbols that meet the VCP criteria
    symbols_meeting_vcp = set()

    for symbol in screened_symbols:
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
                vcp_stock = VCPStock(symbol=symbol, stage=stage)
                db.add(vcp_stock)
                db.commit()

    # Remove stocks that no longer meet the VCP criteria
    existing_vcp_stocks = db.query(VCPStock).all()
    for stock in existing_vcp_stocks:
        if stock.symbol not in symbols_meeting_vcp:
            db.delete(stock)
    db.commit()

def analyze_vcp(data):
    # Parameters
    min_contractions = 2  # Minimum number of contractions
    contraction_threshold = 0.10  # Minimum contraction size (10%)
    contraction_decrease_tolerance = 0.05  # Allowable deviation for decreasing contractions
    volume_decrease_tolerance = 0.05  # Allowable deviation for decreasing volume

    # Find swing highs and lows
    data['swing_high'] = data['high'][(data['high'] > data['high'].shift(1)) & (data['high'] > data['high'].shift(-1))]
    data['swing_low'] = data['low'][(data['low'] < data['low'].shift(1)) & (data['low'] < data['low'].shift(-1))]

    # Extract swing highs and lows with dates
    swing_highs = data.dropna(subset=['swing_high'])
    swing_lows = data.dropna(subset=['swing_low'])

    # Ensure we have matching swing highs and lows
    if swing_highs.empty or swing_lows.empty:
        return False, None

    # Pair swing highs and lows
    swings = []
    i = j = 0
    while i < len(swing_highs) and j < len(swing_lows):
        high_date = swing_highs.index[i]
        low_date = swing_lows.index[j]
        if high_date < low_date:
            swings.append({'high_date': high_date, 'high': swing_highs['swing_high'][high_date]})
            i += 1
        else:
            swings.append({'low_date': low_date, 'low': swing_lows['swing_low'][low_date]})
            j += 1

    # Remove incomplete pairs and calculate contractions and volume
    contractions = []
    volume_during_contractions = []
    for k in range(1, len(swings) - 1, 2):
        if 'high' in swings[k - 1] and 'low' in swings[k]:
            prev_high = swings[k - 1]['high']
            curr_low = swings[k]['low']
            contraction = (prev_high - curr_low) / prev_high
            contractions.append(contraction)

            # Volume during contraction
            start_date = swings[k - 1]['high_date']
            end_date = swings[k]['low_date']
            avg_volume = data.loc[start_date:end_date]['volume'].mean()
            volume_during_contractions.append(avg_volume)

    if len(contractions) < min_contractions:
        return False, None

    # Check for decreasing contractions
    decreasing_contractions = True
    for i in range(1, len(contractions)):
        if contractions[i] > contractions[i - 1] + contraction_decrease_tolerance:
            decreasing_contractions = False
            break

    if not decreasing_contractions:
        return False, None

    # Check contraction sizes
    if any(c < contraction_threshold for c in contractions):
        return False, None

    # Check for decreasing volume during contractions
    decreasing_volume = True
    for i in range(1, len(volume_during_contractions)):
        if volume_during_contractions[i] > volume_during_contractions[i - 1] + volume_decrease_tolerance * volume_during_contractions[i - 1]:
            decreasing_volume = False
            break

    if not decreasing_volume:
        return False, None

    # Determine stage
    if len(contractions) >= 4:
        stage = 'MATURE'
    else:
        stage = 'EARLY'

    return True, stage
