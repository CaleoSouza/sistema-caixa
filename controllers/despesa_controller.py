"""
despesa_controller.py - Lógica de negócio para o módulo de Despesas.
"""

from models.despesa_model import (
    listar_despesas,
    buscar_por_id,
    inserir_despesa,
    atualizar_despesa,
    excluir_despesa,
    resumo_por_mes,
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
