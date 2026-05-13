from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, User

auth_router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

class AuthSchema(BaseModel):
    correo: str
    password: str
    nombre: str = None
    telefono: str = None

@auth_router.post("/register")
async def register(user: AuthSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.correo == user.correo).first():
        raise HTTPException(status_code=400, detail="Ya existe")
    nuevo = User(
        nombre=user.nombre,
        correo=user.correo,
        password=user.password,
        telefono=user.telefono,
    )
    db.add(nuevo); db.commit()
    return {"msg": "Registrado"}

@auth_router.post("/login")
async def login(user: AuthSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.correo == user.correo).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Error")
    return {"student_id": db_user.correo, "nombre": db_user.nombre}