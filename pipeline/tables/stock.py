import enum

from sqlalchemy import Table, Column, Integer, Date, Float, Index, MetaData, Text

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

# This is automatically collected my the sqla metadata and will be created automatically if we
# use table.create(engine)
stock_table_indexes = [
    # TODO check if this is used since a unique index on primary key (name, date) is created also
    Index('idx_name_date', stock_table.c.name, stock_table.c.date, postgresql_using='btree')
]


stock_table_definition = TableDefinition(
    table=stock_table,
    indexes_list=stock_table_indexes,
)
