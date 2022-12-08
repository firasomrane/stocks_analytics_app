from sqlalchemy import Column, Date, Float, Integer, Text

from apis.database import Base


class Stock(Base):
    __tablename__ = 'stock'

    name = Column(Text, primary_key=True)
    date = Column(Date, primary_key=True)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Integer)
    market = Column(Text)
