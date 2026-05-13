from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./keystone.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    correo = Column(String, unique=True, index=True)
    password = Column(String)
    telefono = Column(String, nullable=True)

class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String)
    sender = Column(String)
    text = Column(Text)
    risk_level = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def create_tables():
    Base.metadata.create_all(bind=engine)
    # Migración suave: si la columna "telefono" no existe en una BD vieja, la añadimos
    try:
        with engine.connect() as conn:
            cols = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            col_names = {c[1] for c in cols}
            if "telefono" not in col_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN telefono VARCHAR"))
                conn.commit()
    except Exception as e:
        # No bloqueamos el arranque por un fallo de migración
        print(f"[migración] aviso: {e}")

#para correr la web tenemos que: cd backend y luego: python -m uvicorn main:app --reload