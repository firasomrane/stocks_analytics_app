from pydantic import BaseModel


class StockMetric(BaseModel):
    date: str
    metric: str

    class Config:
        orm_mode = True
