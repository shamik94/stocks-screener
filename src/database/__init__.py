# src/database/__init__.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Fallback to local settings if DATABASE_URL is not set
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'stockdata')
    DB_USER = os.environ.get('DB_USER', 'user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
