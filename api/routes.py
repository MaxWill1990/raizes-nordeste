from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from domain.enums import CanalPedido
from domain.schemas import (
    UsuarioCreate, LoginRequest, PedidoCreate, PagamentoMockInput, AtualizarStatusInput
)
from infrastructure.database import get_db
from infrastructure.models import (
    UsuarioModel, ProdutoModel, PedidoModel, ItemPedidoModel, PagamentoModel, LogAuditoriaModel
)
from application.services import (
    gerar_hash_senha, verificar_senha, criar_token_jwt, registrar_log, obter_usuario_logado
)

router = APIRouter()

@router.post("/auth/usuarios", status_code=201, tags=["Autenticação e Usuários"])
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if not dados.consentimento_lgpd:
        raise HTTPException(status_code=422, detail="O consentimento da LGPD é obrigatório.")
    if db.query(UsuarioModel).filter(UsuarioModel.email == dados.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado no sistema.")
    novo = UsuarioModel(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=dados.perfil.value,
        consentimento_lgpd=dados.consentimento_lgpd
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    registrar_log(db, "CADASTRO_USUARIO", f"Usuário ID {novo.id} ({novo.perfil}) cadastrado.")
    return {"id": novo.id, "nome": novo.nome, "email": novo.email, "perfil": novo.perfil}

@router.post("/auth/login", tags=["Autenticação e Usuários"])
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = criar_token_jwt(usuario.id, usuario.email, usuario.perfil)
    registrar_log(db, "LOGIN", f"Login realizado pelo usuário ID {usuario.id}.")
    return {
        "accessToken": token,
        "tokenType": "Bearer",
        "expiresIn": 7200,
        "user": {"id": usuario.id, "nome": usuario.nome, "perfil": usuario.perfil}
    }

@router.get("/produtos", tags=["Cardápio e Estoque"])
def listar_produtos(
    unidadeId: int = Query(1), page: int = Query(1, ge=1), limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    produtos = db.query(ProdutoModel).filter(ProdutoModel.unidade_id == unidadeId).offset(offset).limit(limit).all()
    return {"page": page, "limit": limit, "itens": produtos}

@router.post("/pedidos", status_code=201, tags=["Pedidos (Fluxo Crítico)"])
def criar_pedido(
    dados: PedidoCreate,
    usuario: dict = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    valor_total = 0.0
    itens_para_salvar = []

    for item in dados.itens:
        produto = db.query(ProdutoModel).filter(ProdutoModel.id == item.produtoId).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto ID {item.produtoId} não encontrado.")
        if produto.estoque < item.quantidade:
            raise HTTPException(
                status_code=409,
                detail=f"Estoque insuficiente para '{produto.nome}'. Disponível: {produto.estoque}."
            )
        produto.estoque -= item.quantidade
        valor_total += produto.preco * item.quantidade
        itens_para_salvar.append((produto.id, item.quantidade, produto.preco))

    novo_pedido = PedidoModel(
        cliente_id=int(usuario["sub"]),
        unidade_id=dados.unidadeId,
        canal_pedido=dados.canalPedido.value,
        status="AGUARDANDO_PAGAMENTO",
        total=round(valor_total, 2)
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)

    for prod_id, qtd, preco in itens_para_salvar:
        db.add(ItemPedidoModel(pedido_id=novo_pedido.id, produto_id=prod_id, quantidade=qtd, preco_unitario=preco))
    db.commit()

    registrar_log(db, "CRIAR_PEDIDO", f"Pedido {novo_pedido.id} criado via canal {novo_pedido.canal_pedido}.")
    return {
        "pedidoId": novo_pedido.id,
        "canalPedido": novo_pedido.canal_pedido,
        "status": novo_pedido.status,
        "total": novo_pedido.total,
        "criadoEm": novo_pedido.criado_em
    }

@router.get("/pedidos", tags=["Pedidos (Fluxo Crítico)"])
def listar_pedidos(
    canalPedido: Optional[CanalPedido] = Query(None, description="Filtrar por canal (APP, TOTEM, BALCAO, PICKUP, WEB)"),
    usuario: dict = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    consulta = db.query(PedidoModel)
    if canalPedido:
        consulta = consulta.filter(PedidoModel.canal_pedido == canalPedido.value)
    return consulta.all()

@router.post("/pagamentos/{pedido_id}/mock", tags=["Pagamentos (Mock)"])
def processar_pagamento_mock(
    pedido_id: int,
    dados: PagamentoMockInput,
    usuario: dict = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    status_pgto = "APROVADO" if dados.aprovar else "RECUSADO"
    pedido.status = "EM_PREPARO" if dados.aprovar else "CANCELADO"

    pagamento = PagamentoModel(
        pedido_id=pedido.id,
        forma_pagamento=dados.formaPagamento,
        status_pagamento=status_pgto
    )
    db.add(pagamento)
    db.commit()

    registrar_log(db, "PAGAMENTO_MOCK", f"Pedido {pedido.id}: pagamento {status_pgto} -> Status {pedido.status}.")
    return {
        "pedidoId": pedido.id,
        "statusPagamento": status_pgto,
        "novoStatusPedido": pedido.status,
        "mensagem": "Pagamento confirmado e enviado para a cozinha!" if dados.aprovar else "Pagamento recusado pelo gateway mock."
    }

@router.patch("/pedidos/{pedido_id}/status", tags=["Pedidos (Fluxo Crítico)"])
def atualizar_status_pedido(
    pedido_id: int,
    dados: AtualizarStatusInput,
    usuario: dict = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    if usuario.get("perfil") not in ["GERENTE", "ADMIN", "ATENDENTE"]:
        raise HTTPException(status_code=403, detail="Acesso negado: apenas funcionários podem mudar o status.")
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    pedido.status = dados.novoStatus.value
    db.commit()
    registrar_log(db, "ATUALIZAR_STATUS", f"Pedido {pedido.id} alterado para {pedido.status} por {usuario.get('email')}.")
    return {"pedidoId": pedido.id, "novoStatus": pedido.status}

@router.get("/auditoria/logs", tags=["Segurança e Auditoria (LGPD)"])
def listar_logs_auditoria(
    usuario: dict = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    if usuario.get("perfil") not in ["GERENTE", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Apenas GERENTE ou ADMIN podem consultar logs de auditoria.")
    return db.query(LogAuditoriaModel).order_by(LogAuditoriaModel.id.desc()).all()