from sqlalchemy import Column, Integer, String, create_engine, text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func  # สำหรับ func.now()

Base = declarative_base()
engine = create_engine("postgresql://admin:it%40apico4U@10.10.10.181:5432/license_logsdb")

schemas = ["autoform", "nx", "catia", "solidworks","autodesk"]

# สร้าง schema
with engine.connect() as conn:
    for schema_name in schemas:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    conn.commit()

# สร้าง table raws ในแต่ละ schema
for schema_name in schemas:
    class Log(Base):
        __tablename__ = "raws"
        __table_args__ = {"schema": schema_name}  # กำหนด schema

        id = Column(Integer, primary_key=True)
        name = Column(String)
        data = Column(JSONB)
        created_at = Column(DateTime, server_default=func.now())

# สร้าง table ใน DB
class nx(Base):
    __tablename__ = "session_logs"
    start_date = Column(Date)
    id = Column(Integer, primary_key=True)
    start_time = Column(Time)
    end_date = Column(Date)
    end_time = Column(Time)
    duration_minutes = Column(Numeric(10,2))
    hostname = Column(String)
    module = Column(String)
    username = Column(String)


class autoform(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    start_date = Column(Date)
    start_time = Column(Time)
    start_hours = Column(Integer)
    start_action = Column(String)
    end_date = Column(Date)
    end_time = Column(Time)
    end_hours = Column(Integer)
    end_action = Column(String)
    duration_minutes = Column(Numeric(10,2))
    host = Column(String)
    module = Column(String)
    username = Column(String)
    version = Column(String)


class solidwork(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    start_date = Column(Date)
    start_time = Column(Time)
    end_date = Column(Date)
    end_time = Column(Time)
    duration_minutes = Column(Numeric(10,2))
    feature = Column(String)
    username = Column(String)
    computer = Column(String)


Base.metadata.create_all(bind=engine)

print("All schemas and tables created successfully!")
