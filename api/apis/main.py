from fastapi import Depends, FastAPI, Query
from pydantic import Required
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


# TODO add response type as Pydantic class # , response_model=list[StockMetric]
@app.get('/stock_metrics/')
def read_stock_metric(
    ticker: str = Query(default=Required, min_length=1, max_length=5),
    start: str = Query(default=Required, regex=r'^(\d{4})-(\d{2})-(\d{2}?)', format='date'),
    end: str = Query(default=Required, regex=r'^(\d{4})-(\d{2})-(\d{2}?)', format='date'),
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
