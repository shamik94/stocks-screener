# src/main.py
import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database import Base, engine, SessionLocal
from src.controller.api import router as api_router
from src.service.screener_service import run_screening
from src.service.vcp_service import run_vcp_detection

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API router
app.include_router(api_router)  # Remove the prefix if it wasn't there before

# Debug: Print all registered routes
@app.on_event("startup")
async def startup_event():
    print("Registered routes:")
    for route in app.routes:
        print(f"{route.methods} {route.path}")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
