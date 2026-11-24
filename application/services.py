from datetime import datetime, timedelta
import bcrypt
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from infrastructure.models import UsuarioModel, ProdutoModel, LogAuditoriaModel

SECRET_KEY = "chave_secreta_raizes_nordeste_uninter"
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))

def criar_token_jwt(usuario_id: int, email: str, perfil: str) -> str:
    expiracao = datetime.utcnow() + timedelta(hours=2)
    payload = {"sub": str(usuario_id), "email": email, "perfil": perfil, "exp": expiracao}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def registrar_log(db: Session, acao: str, detalhes: str):
    novo_log = LogAuditoriaModel(acao=acao, detalhes=detalhes)
    db.add(novo_log)
    db.commit()

def obter_usuario_logado(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
):
    if not credenciais:
        raise HTTPException(status_code=401, detail="Token de autenticação não informado.")
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

def popular_dados_iniciais(db: Session):
    # Cria usuários e cardápio inicial se o banco estiver vazio (Seed)
    if db.query(UsuarioModel).count() == 0:
        cliente = UsuarioModel(
            nome="Maria Cliente",
            email="cliente@exemplo.com",
            senha_hash=gerar_hash_senha("Senha@123"),
            perfil="CLIENTE",
            consentimento_lgpd=True
        )
        gerente = UsuarioModel(
            nome="João Gerente",
            email="gerente@exemplo.com",
            senha_hash=gerar_hash_senha("Senha@123"),
            perfil="GERENTE",
            consentimento_lgpd=True
        )
        db.add_all([cliente, gerente])

    if db.query(ProdutoModel).count() == 0:
        pratos = [
            ProdutoModel(nome="Cuscuz Recheado com Carne de Sol", preco=24.90, estoque=15, unidade_id=1),
            ProdutoModel(nome="Tapioca de Queijo Coalho", preco=16.50, estoque=20, unidade_id=1),
            ProdutoModel(nome="Bolo de Macaxeira com Café", preco=14.00, estoque=5, unidade_id=1),
        ]
        db.add_all(pratos)
    db.commit()