"""
cliente_controller.py - Lógica de negócio para Clientes.
Intermediário entre a view e o model. Valida dados antes de persistir.
"""

import os
import time
import logging

from PIL import Image

from models.cliente_model import (
    listar_clientes,
    listar_em_atraso,
    buscar_por_id,
    buscar_por_cpf,
    resumo_clientes,
    inserir_cliente,
    atualizar_cliente,
    excluir_cliente,
)
from utils import desformatar_moeda

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Caminhos de fotos dos clientes
# ------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_FOTOS_CLIENTES = os.path.join(_BASE_DIR, "imagens", "clientes")


# ------------------------------------------------------------------
# Consultas
# ------------------------------------------------------------------

def obter_lista(busca: str = "") -> list:
    """Retorna clientes com o campo 'status_credito' calculado."""
    clientes = listar_clientes(busca)
    for c in clientes:
        c["status_credito"] = _calcular_status(c)
    return clientes


def obter_em_atraso() -> list:
    """Retorna clientes com débito pendente e status calculado."""
    clientes = listar_em_atraso()
    for c in clientes:
        c["status_credito"] = _calcular_status(c)
    return clientes


def obter_resumo() -> dict:
    """Retorna os dados dos 3 cards da tela de clientes."""
    return resumo_clientes()


def obter_por_id(cliente_id: int) -> dict | None:
    """Retorna um cliente pelo ID com status calculado."""
    c = buscar_por_id(cliente_id)
    if c:
        c["status_credito"] = _calcular_status(c)
    return c


# ------------------------------------------------------------------
# Gravação
# ------------------------------------------------------------------

def salvar(dados: dict, cliente_id: int = None) -> tuple[bool, str]:
    """
    Cria ou atualiza um cliente após validação.
    Retorna (sucesso: bool, mensagem: str).
    """
    ok, msg = _validar(dados, cliente_id)
    if not ok:
        return False, msg

    if cliente_id:
        ok = atualizar_cliente(cliente_id, dados)
        return ok, "Cliente atualizado com sucesso!" if ok else "Erro ao atualizar cliente."
    else:
        novo_id = inserir_cliente(dados)
        log.info(f"Cliente '{dados.get('nome')}' cadastrado com id={novo_id}.")
        return True, "Cliente cadastrado com sucesso!"


def remover(cliente_id: int) -> tuple[bool, str]:
    """Exclusão lógica do cliente."""
    excluir_cliente(cliente_id)
    log.info(f"Cliente id={cliente_id} removido.")
    return True, "Cliente removido com sucesso!"


def salvar_foto_cliente(caminho_origem: str, foto_atual: str = None) -> str | None:
    """
    Copia a foto do cliente para imagens/clientes/, redimensiona e retorna o nome do arquivo.
    Remove a foto anterior se existir.
    """
    try:
        os.makedirs(PASTA_FOTOS_CLIENTES, exist_ok=True)

        # Remove foto anterior se existir
        if foto_atual:
            antigo = os.path.join(PASTA_FOTOS_CLIENTES, foto_atual)
            if os.path.exists(antigo):
                os.remove(antigo)

        # Redimensiona mantendo proporção (max 400x400) e salva com nome único
        img = Image.open(caminho_origem).convert("RGB")
        img.thumbnail((400, 400), Image.LANCZOS)

        base, ext = os.path.splitext(os.path.basename(caminho_origem))
        nome_final = f"{base}_{int(time.time())}{ext}"
        destino = os.path.join(PASTA_FOTOS_CLIENTES, nome_final)
        img.save(destino, quality=85)
        return nome_final
    except Exception as e:
        log.error(f"Erro ao salvar foto do cliente: {e}")
        return None


def excluir_foto_cliente(foto_nome: str):
    """Remove o arquivo de foto do disco."""
    if not foto_nome:
        return
    caminho = os.path.join(PASTA_FOTOS_CLIENTES, foto_nome)
    if os.path.exists(caminho):
        os.remove(caminho)


# ------------------------------------------------------------------
# Auxiliares internos
# ------------------------------------------------------------------

def _calcular_status(cliente: dict) -> str:
    """
    Retorna o status de crédito do cliente:
    'sem_debitos' | 'em_dia' | 'em_atraso'

    Regra: somente considera 'em_atraso' se o cliente tiver débito E
    pelo menos um item anotado há mais de 30 dias sem quitação.
    Itens anotados há <= 30 dias ficam como 'em_dia'.
    """
    if not cliente.get("tem_crediario"):
        return "sem_debitos"
    if (cliente.get("debito_atual") or 0) <= 0:
        return "em_dia"
    # Tem débito — verifica se algum item tem mais de 30 dias
    from models.crediario_model import tem_debito_em_atraso
    if tem_debito_em_atraso(cliente["id"]):
        return "em_atraso"
    return "em_dia"


def _validar(dados: dict, cliente_id: int = None) -> tuple[bool, str]:
    """Validação dos dados do cliente, incluindo CPF único."""
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return False, "O nome do cliente é obrigatório."
    if len(nome) < 2:
        return False, "O nome deve ter ao menos 2 caracteres."

    # Verifica CPF duplicado (ignora se CPF não foi informado)
    cpf = (dados.get("cpf") or "").strip()
    if cpf:
        existente = buscar_por_cpf(cpf, excluir_id=cliente_id)
        if existente:
            return False, f"CPF já cadastrado para o cliente '{existente['nome']}' (ID {existente['id']})."

    return True, ""
