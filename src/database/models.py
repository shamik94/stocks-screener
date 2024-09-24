# src/database/models.py

from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    country = Column(String)

class ScreenedStock(Base):
    __tablename__ = 'screened_stocks'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    country = Column(String, nullable=False)

class VCPStock(Base):
    __tablename__ = 'vcp_stocks'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    stage = Column(String)
    country = Column(String)  # Add this line to include the country attribute
    detected_date = Column(Date)
