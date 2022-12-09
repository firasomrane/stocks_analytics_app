from database.utils import get_db_config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

STOCK_MARKET_DATA = 'stock_market_data'

SQLALCHEMY_DATABASE_URL = get_db_config(db_name=STOCK_MARKET_DATA).uri

db_engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

Base = declarative_base()
