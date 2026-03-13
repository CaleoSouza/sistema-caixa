"""
despesa_controller.py - Lógica de negócio para o módulo de Despesas.
"""

import datetime
from models.despesa_model import (
    listar_despesas,
    buscar_por_id,
    inserir_despesa,
    atualizar_despesa,
    excluir_despesa,
    resumo_por_mes,
    # Auto
    listar_despesas_auto,
    buscar_auto_por_id,
    inserir_despesa_auto,
    atualizar_despesa_auto,
    excluir_despesa_auto,
    gerar_despesas_mes,
)

# Status disponíveis: chave interna → rótulo exibido
STATUS_LABELS = {
    "pago":      "Pago",
    "agendado":  "Agendado",
    "em_aberto": "Em Aberto",
}

# Formas de pagamento disponíveis
FORMAS_PAGAMENTO = ["Dinheiro", "PIX", "Boleto", "Cartão", "Transferência", "Anotado"]


def obter_lista(busca: str = "", mes: int = 0, ano: int = 0, status: str = "") -> list[dict]:
    """Retorna despesas filtradas e traduz o status para exibição."""
    despesas = listar_despesas(busca=busca, mes=mes, ano=ano, status=status)
    for d in despesas:
        d["status_label"] = STATUS_LABELS.get(d["status"], d["status"])
    return despesas


def obter_resumo(mes: int, ano: int) -> dict:
    """Retorna os totais por status para o mês/ano informado."""
    return resumo_por_mes(mes, ano)


def salvar(dados: dict) -> tuple[bool, str]:
    """
    Valida e salva (insere ou atualiza) uma despesa.
    Retorna (True, id) em caso de sucesso ou (False, mensagem_erro).
    """
    descricao = dados.get("descricao", "").strip()
    data      = dados.get("data", "").strip()
    valor_str = str(dados.get("valor", "")).strip().replace(",", ".")

    if not descricao:
        return False, "A descrição é obrigatória."
    if not data:
        return False, "A data é obrigatória."
    try:
        valor = float(valor_str)
        if valor < 0:
            raise ValueError
    except ValueError:
        return False, "Digite um valor válido (número positivo)."

    registro = {
        "descricao":       descricao,
        "data":            data,
        "responsavel":     dados.get("responsavel", "").strip(),
        "valor":           valor,
        "forma_pagamento": dados.get("forma_pagamento", "Dinheiro"),
        "status":          dados.get("status", "em_aberto"),
    }

    despesa_id = dados.get("id")
    if despesa_id:
        atualizar_despesa(despesa_id, registro)
        return True, str(despesa_id)
    else:
        novo_id = inserir_despesa(registro)
        return True, str(novo_id)


def remover(despesa_id: int) -> tuple[bool, str]:
    """Remove uma despesa pelo ID."""
    try:
        excluir_despesa(despesa_id)
        return True, "Despesa removida."
    except Exception as e:
        return False, str(e)


def obter_por_id(despesa_id: int) -> dict | None:
    """Retorna os dados de uma despesa pelo ID."""
    return buscar_por_id(despesa_id)


# ==================================================================
# Despesas Automáticas (fixas mensais)
# ==================================================================

def obter_lista_auto() -> list[dict]:
    """Retorna todas as despesas automáticas."""
    return listar_despesas_auto()


def obter_auto_por_id(auto_id: int) -> dict | None:
    """Retorna uma despesa automática pelo ID."""
    return buscar_auto_por_id(auto_id)


def salvar_auto(dados: dict) -> tuple[bool, str]:
    """
    Valida e salva (insere ou atualiza) uma despesa automática.
    Retorna (True, id) ou (False, mensagem_erro).
    """
    descricao = dados.get("descricao", "").strip()
    valor_str = str(dados.get("valor", "")).strip().replace(",", ".")

    if not descricao:
        return False, "A descrição é obrigatória."

    try:
        dia = int(dados.get("dia_mes", 1))
        if not (1 <= dia <= 31):
            raise ValueError
    except (ValueError, TypeError):
        return False, "Informe um dia válido entre 1 e 31."

    try:
        valor = float(valor_str)
        if valor < 0:
            raise ValueError
    except ValueError:
        return False, "Digite um valor válido (número positivo)."

    registro = {
        "descricao":       descricao,
        "dia_mes":         dia,
        "responsavel":     dados.get("responsavel", "").strip(),
        "valor":           valor,
        "forma_pagamento": dados.get("forma_pagamento", "Dinheiro"),
    }

    auto_id = dados.get("id")
    if auto_id:
        atualizar_despesa_auto(auto_id, registro)
        return True, str(auto_id)
    else:
        novo_id = inserir_despesa_auto(registro)
        return True, str(novo_id)


def remover_auto(auto_id: int) -> tuple[bool, str]:
    """Remove uma despesa automática pelo ID."""
    try:
        excluir_despesa_auto(auto_id)
        return True, "Despesa automática removida."
    except Exception as e:
        return False, str(e)


def gerar_despesas_mes_atual() -> int:
    """
    Gera as despesas automáticas para o mês/ano atual.
    Chamado toda vez que a tela de Despesas é aberta.
    Retorna a quantidade de novas despesas geradas.
    """
    hoje = datetime.date.today()
    return gerar_despesas_mes(hoje.month, hoje.year)
