from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from apis.database import SessionLocal
from apis.schemas import StockMetric
from apis.stock_functions import get_stock_metric

app = FastAPI(title='API for stock metrics', version='1-0-0')


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/stock_metrics/')  # , response_model=list[StockMetric]
def read_stock_metric(
    ticker: str = 'AAPL',
    start: str = '2010-10-10',
    end: str = '2011-04-01',
    price_column: str = 'open_price',
    metric: str = 'median',
    rolling_window: int = 10,
    db_session: Session = Depends(get_db),
):

    stock_metrics = get_stock_metric(
        db_session,
        ticker=ticker,
        start=start,
        end=end,
        price_column=price_column,
        metric=metric,
        rolling_window=rolling_window,
    )
    return stock_metrics
