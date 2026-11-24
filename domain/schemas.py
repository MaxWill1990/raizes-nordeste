from typing import List
from pydantic import BaseModel, Field
from domain.enums import CanalPedido, StatusPedido, PerfilUsuario

# Contrato para criar usuário
class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, example="Maria Silva")
    email: str = Field(..., example="cliente@exemplo.com")
    senha: str = Field(..., min_length=6, example="Senha@123")
    perfil: PerfilUsuario = Field(default=PerfilUsuario.CLIENTE)
    consentimento_lgpd: bool = Field(default=True)

# Contrato para fazer Login
class LoginRequest(BaseModel):
    email: str = Field(..., example="cliente@exemplo.com")
    senha: str = Field(..., example="Senha@123")

# Contrato de cada item dentro do pedido
class ItemPedidoInput(BaseModel):
    produtoId: int = Field(..., example=1)
    quantidade: int = Field(..., gt=0, description="Quantidade deve ser maior que zero", example=2)

# Contrato obrigatório da Uninter para criar Pedido (com canalPedido)
class PedidoCreate(BaseModel):
    canalPedido: CanalPedido = Field(..., example=CanalPedido.TOTEM)
    unidadeId: int = Field(default=1, example=1)
    itens: List[ItemPedidoInput]
    formaPagamento: str = Field(default="PIX", example="PIX")

# Contrato para simular o Pagamento Mock (Aprovado ou Recusado)
class PagamentoMockInput(BaseModel):
    formaPagamento: str = Field(default="PIX", example="PIX")
    aprovar: bool = Field(default=True, description="True aprova o pagamento, False simula cartão recusado")

# Contrato para atualizar o status do pedido (Cozinha -> Pronto -> Entregue)
class AtualizarStatusInput(BaseModel):
    novoStatus: StatusPedido = Field(..., example=StatusPedido.EM_PREPARO)