# src/controller/api.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database.models import ScreenedStock, VCPStock
from src.database import SessionLocal
from src.research.support_resistance_detection import detect_and_plot_support_resistance as detect_and_plot_support_resistance_v1
from src.research.support_resistance_detection_v2 import detect_and_plot_support_resistance as detect_and_plot_support_resistance_v2

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
    result = [{'symbol': stock.symbol, 'country': stock.country, 'stage': stock.stage, 'detected_date': stock.detected_date} for stock in stocks]
    return {"vcp_stocks": result}

@router.get("/support_resistance_graph")
def get_support_resistance_graph(
    symbol: str = Query(..., description="Stock symbol"),
    country: str = Query(..., description="Country of the stock"),
    months: int = Query(6, description="Number of months to fetch data")
):
    try:
        graph_data = detect_and_plot_support_resistance_v1(symbol, country, months)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")

@router.get("/support_resistance_graph_v2")
def get_support_resistance_graph_v2(
    symbol: str = Query(..., description="Stock symbol"),
    country: str = Query(..., description="Country of the stock"),
    months: int = Query(6, description="Number of months to fetch data")
):
    try:
        graph_data = detect_and_plot_support_resistance_v2(symbol, country, months)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")