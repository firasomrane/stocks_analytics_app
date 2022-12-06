import enum

from sqlalchemy import Table, Column, Integer, Date, Float, Enum, Index, MetaData, Text

from pipeline.tables.table_definition import TableDefinition

sqla_metadata = MetaData()


class StockExchangeEnum(enum.Enum):
   NASDAQ = 'NASDAQ'
   NYSE = 'NYSE'


stock_table = Table(
   'stock', 
   sqla_metadata, 
   Column('name', Text, primary_key=True), 
   Column('date', Date, primary_key=True), 
   Column('open_price', Float, nullable=False),
   Column('close_price', Float, nullable=False),
   Column('high_price', Float, nullable=False),
   Column('low_price', Float, nullable=False),
   Column('volume', Integer, nullable=False),
   # Column('market', Enum(StockExchangeEnum)),
   Column('market', Text),
)

stock_table_indexes = [
   # Index()
]


stock_table_definition = TableDefinition(
   table=stock_table,
   indexes_list=stock_table_indexes,
)