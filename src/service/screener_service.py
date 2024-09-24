# src/service/screener_service.py

import numpy as np
from sqlalchemy.orm import Session
from src.database.models import StockData, ScreenedStock

def run_screening(db: Session, countries: list):
    # Get a list of all symbols for the specified countries
    symbols = db.query(StockData.symbol).filter(StockData.country.in_(countries)).distinct().all()
    symbols = [s[0] for s in symbols]

    # Keep track of symbols that meet the criteria
    symbols_meeting_criteria = set()

    for symbol in symbols:
        print("Screening for Symbol " + symbol)
        stock_entries = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.date).all()
        if len(stock_entries) < 50:
            # Not enough data even for 50-day moving average
            continue

        # Prepare data
        closes = [entry.close for entry in stock_entries]
        current_price = closes[-1]

        # Calculate moving averages
        ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
        ma_150 = np.mean(closes[-150:]) if len(closes) >= 150 else None
        ma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else None

        # Calculate 52-week high and low
        last_252_closes = closes[-252:] if len(closes) >= 252 else closes
        low_52week = min(last_252_closes) if last_252_closes else None
        high_52week = max(last_252_closes) if last_252_closes else None

        # Screening criteria checks
        criteria_passed = True

        # Check if moving averages exist
        if ma_50 is None or ma_150 is None or ma_200 is None:
            continue  # Not enough data for high precision

        # Criteria 1: Price above its 50-day, 150-day, and 200-day moving averages
        if current_price < ma_50 or current_price < ma_150 or current_price < ma_200:
            criteria_passed = False

        # Criteria 2: 50-day MA above 150-day MA
        if ma_50 < ma_150:
            criteria_passed = False

        # Criteria 3: 150-day MA above 200-day MA
        if ma_150 < ma_200:
            criteria_passed = False

        # Criteria 5: Price at least 30% above its 52-week low
        if low_52week and current_price < 1.3 * low_52week:
            criteria_passed = False

        # Criteria 6: Price within 25% of its 52-week high
        if high_52week and current_price < 0.75 * high_52week:
            criteria_passed = False

        if criteria_passed:
            symbols_meeting_criteria.add(symbol)

            # Check if the stock is already in screened_stocks
            exists = db.query(ScreenedStock).filter(ScreenedStock.symbol == symbol).first()
            if not exists:
                # Add new screened stock
                country = stock_entries[0].country if stock_entries[0].country else 'unknown'
                screened_stock = ScreenedStock(symbol=symbol, country=country)
                db.add(screened_stock)

    db.commit()

    # Remove stocks that no longer meet the criteria for the specified countries
    existing_screened_stocks = db.query(ScreenedStock).filter(ScreenedStock.country.in_(countries)).all()
    for stock in existing_screened_stocks:
        if stock.symbol not in symbols_meeting_criteria:
            db.delete(stock)

    db.commit()
