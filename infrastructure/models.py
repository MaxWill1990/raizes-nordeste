from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database import Base

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, default="CLIENTE")
    consentimento_lgpd = Column(Boolean, default=True)

class ProdutoModel(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    unidade_id = Column(Integer, default=1)

class PedidoModel(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))
    unidade_id = Column(Integer, default=1)
    canal_pedido = Column(String, nullable=False)  # APP, TOTEM, BALCAO, PICKUP, WEB
    status = Column(String, default="AGUARDANDO_PAGAMENTO")
    total = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    itens = relationship("ItemPedidoModel", back_populates="pedido")

class ItemPedidoModel(Base):
    __tablename__ = "itens_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    pedido = relationship("PedidoModel", back_populates="itens")

class PagamentoModel(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    forma_pagamento = Column(String, nullable=False)
    status_pagamento = Column(String, nullable=False)  # APROVADO ou RECUSADO
    criado_em = Column(DateTime, default=datetime.utcnow)

class LogAuditoriaModel(Base):
    __tablename__ = "logs_auditoria"
    id = Column(Integer, primary_key=True, index=True)
    acao = Column(String, nullable=False)
    detalhes = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)