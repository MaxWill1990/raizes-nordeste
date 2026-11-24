from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from infrastructure.database import Base, engine, SessionLocal
from application.services import popular_dados_iniciais
from api.routes import router

# Cria as tabelas no SQLite e insere os dados iniciais (Seed)
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    popular_dados_iniciais(db)

app = FastAPI(
    title="API Raízes do Nordeste",
    description="Back-end Multicanal (App, Totem, Balcão, Pick-up, Web) - Projeto Uninter",
    version="1.0.0"
)

# Padrão único de erro JSON exigido no Roteiro (página 20)
@app.exception_handler(HTTPException)
async def tratar_erro_http(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": [],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao(request: Request, exc: RequestValidationError):
    detalhes = [{"field": str(e["loc"][-1]), "issue": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "error": "ERRO_VALIDACAO",
            "message": "Dados de entrada inválidos ou campo obrigatório ausente.",
            "details": detalhes,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": request.url.path
        }
    )

@app.get("/health", tags=["Status"])
def verificar_servidor():
    return {"status": "online", "rede": "Raízes do Nordeste"}

app.include_router(router)