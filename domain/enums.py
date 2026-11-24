from enum import Enum

class CanalPedido(str, Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

class StatusPedido(str, Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

class PerfilUsuario(str, Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"