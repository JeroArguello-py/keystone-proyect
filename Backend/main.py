from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables
from services.chat_service import chat_router
from services.auth_service import auth_router
from services.analysis_service import analysis_router
app = FastAPI(title="CampusCare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(analysis_router, prefix="/api/analysis")

@app.get("/")
def home():
    return {"status": "Servidor Keystone Activo"}