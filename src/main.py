# src/main.py

import uvicorn
from fastapi import FastAPI
from src.database import Base, engine, SessionLocal
from src.controller.api import router as api_router
from src.service.screener_service import run_screening
from src.service.vcp_service import run_vcp_detection

app = FastAPI()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

@app.on_event("startup")
async def startup_event():
    init_db()

    print("Running screening service...")
    db = SessionLocal()
    run_screening(db, countries=['india,usa'])
    db.close()
    print("Screening completed.")

    print("Running VCP detection service...")
    db = SessionLocal()
    run_vcp_detection(db, countries=['india,usa'])
    db.close()
    print("VCP detection completed.")

# Include API routers
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
