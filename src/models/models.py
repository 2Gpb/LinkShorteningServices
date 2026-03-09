from sqlalchemy import (
    Integer, 
    MetaData, 
    Table, 
    Column, 
    Integer, 
    String, 
    Boolean, 
    DateTime, 
    ForeignKey, 
    text
)

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

links = Table(
    "links",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("original_url", String, nullable=False, index=True),
    Column("short_code", String, nullable=False, unique=True, index=True),

    Column("created_at", DateTime, nullable=False),
    Column("expires_at", DateTime, nullable=True),

    Column("click_count", Integer, nullable=False, server_default=text("0")),
    Column("last_used_at", DateTime, nullable=True),

    Column("owner_id", Integer, ForeignKey("user.id"), nullable=True),
)