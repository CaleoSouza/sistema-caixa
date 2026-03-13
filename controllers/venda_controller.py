"""
venda_controller.py - Lógica de negócio para o Carrinho e Vendas.
Intermediário entre a view e os models. Valida dados antes de persistir.
"""

import logging
from datetime import date

from models.venda_model import registrar_venda, listar_vendas, listar_itens_venda
from models.produto_model import buscar_por_id
from models.crediario_model import inserir_item as inserir_item_crediario
from database import conectar

log = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Finalização de venda
# ------------------------------------------------------------------

def finalizar_venda(
    itens_carrinho: list,
    cliente_id: int | None,
    forma_pagamento: str,
    desconto_pct: float,
    taxa_cartao: float = 0.0,
    parcelas: int = 1,
) -> tuple[bool, str]:
    """
    Finaliza uma venda completa:
    1. Valida estoque de cada item
    2. Registra venda + itens no banco
    3. Baixa estoque de cada produto vendido
    4. Se forma_pagamento == 'a_prazo', insere itens no crediário do cliente

    Retorna (sucesso: bool, mensagem: str).
    """
    if not itens_carrinho:
        return False, "O carrinho está vazio."

    # ------------------------------------------------------------------
    # Validação de estoque
    # ------------------------------------------------------------------
    for item in itens_carrinho:
        p = buscar_por_id(item["produto_id"])
        if not p:
            return False, f"Produto #{item['produto_id']} não encontrado no banco."
        if p["quantidade"] < item["quantidade"]:
            return False, (
                f"Estoque insuficiente para '{p['nome']}': "
                f"disponível {p['quantidade']}, pedido {item['quantidade']}."
            )

    # ------------------------------------------------------------------
    # Calcula totais
    # ------------------------------------------------------------------
    total        = round(sum(i["subtotal"] for i in itens_carrinho), 2)
    desconto_val = round(total * desconto_pct / 100, 2)
    total_final  = round(total - desconto_val, 2)

    dados_venda = {
        "cliente_id":      cliente_id,
        "total":           total,
        "desconto":        desconto_val,
        "total_final":     total_final,
        "forma_pagamento": forma_pagamento,
        "taxa_cartao":     taxa_cartao,
        "parcelas":        parcelas,
    }

    # ------------------------------------------------------------------
    # Registra venda + itens no banco
    # ------------------------------------------------------------------
    venda_id = registrar_venda(dados_venda, itens_carrinho)

    # ------------------------------------------------------------------
    # Baixa estoque — se falhar, cancela a venda registrada
    # ------------------------------------------------------------------
    try:
        conn = conectar()
        for item in itens_carrinho:
            conn.execute(
                "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        conn.commit()
        conn.close()
    except Exception as exc:  # pragma: no cover
        log.error("Erro ao baixar estoque após venda #%d: %s", venda_id, exc)
        return False, f"Venda registrada mas houve erro ao atualizar estoque: {exc}"

    # ------------------------------------------------------------------
    # Registra no crediário — se falhar, estoque já foi baixado mas
    # o operador é alertado para corrigir manualmente
    # ------------------------------------------------------------------
    if forma_pagamento == "a_prazo" and cliente_id:
        data_hoje = date.today().strftime("%d/%m/%Y")
        try:
            for item in itens_carrinho:
                inserir_item_crediario({
                    "cliente_id":     cliente_id,
                    "produto_nome":   item["nome"],
                    "data":           data_hoje,
                    "quantidade":     item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                    "total":          item["subtotal"],
                })
        except Exception as exc:  # pragma: no cover
            log.error("Erro ao lançar crediário para venda #%d: %s", venda_id, exc)
            return (
                False,
                f"Venda #{venda_id:02d} registrada mas houve erro ao lançar crediário: {exc}",
            )

    log.info(
        "Venda #%02d finalizada | Total: R$ %.2f | Desconto: R$ %.2f | "
        "Forma: %s | Taxa cartão: %.2f%% | Parcelas: %dx",
        venda_id, total_final, desconto_val,
        forma_pagamento, taxa_cartao, parcelas,
    )

    return True, f"Venda #{venda_id:02d} registrada com sucesso!"


# ------------------------------------------------------------------
# Consultas para Relatórios (Etapa 5)
# ------------------------------------------------------------------

def obter_vendas(limite: int = 100) -> list:
    """Retorna as últimas vendas com nome do cliente."""
    return listar_vendas(limite)


def obter_itens_venda(venda_id: int) -> list:
    """Retorna os itens de uma venda específica."""
    return listar_itens_venda(venda_id)
