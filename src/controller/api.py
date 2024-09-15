# src/controller/api.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.models import ScreenedStock, VCPStock
from src.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/screened_stocks")
def get_screened_stocks(db: Session = Depends(get_db)):
    stocks = db.query(ScreenedStock).all()
    result = [{'symbol': stock.symbol, 'country': stock.country} for stock in stocks]
    return {"screened_stocks": result}

@router.get("/vcp_stocks")
def get_vcp_stocks(db: Session = Depends(get_db)):
    stocks = db.query(VCPStock).all()
    result = [{'symbol': stock.symbol, 'stage': stock.stage, 'detected_date': stock.detected_date} for stock in stocks]
    return {"vcp_stocks": result}
