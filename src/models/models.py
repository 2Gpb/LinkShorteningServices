from sqlalchemy import Integer, MetaData, Table, Column, Integer, String, Boolean

metadata = MetaData()

user = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String, nullable=False),
    Column('username', String, nullable=False),
    Column('hashed_password', String, nullable=False),

    Column("is_active", Boolean, nullable=False, default=True),
    Column("is_superuser", Boolean, nullable=False, default=False),
    Column("is_verified", Boolean, nullable=False, default=False),
)