"""
produto_controller.py - Lógica de negócio para Produtos.
Intermediário entre a view e o model. Valida dados antes de persistir.
"""

from models.produto_model import (
    listar_produtos,
    buscar_por_id,
    inserir_produto,
    atualizar_produto,
    excluir_produto,
    resumo_produtos,
)


# ------------------------------------------------------------------
# Consultas
# ------------------------------------------------------------------

def obter_lista(busca: str = "") -> list:
    """Retorna produtos com o campo 'status_estoque' calculado."""
    produtos = listar_produtos(busca)
    for p in produtos:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return produtos


def obter_resumo() -> dict:
    """Retorna os dados dos 5 cards da tela de produtos."""
    return resumo_produtos()


def obter_por_id(produto_id: int) -> dict | None:
    """Retorna um produto pelo ID com status calculado."""
    p = buscar_por_id(produto_id)
    if p:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return p


# ------------------------------------------------------------------
# Gravação
# ------------------------------------------------------------------

def salvar(dados: dict, produto_id: int = None) -> tuple[bool, str]:
    """
    Cria ou atualiza um produto após validação.
    Retorna (sucesso: bool, mensagem: str).
    """
    ok, msg = _validar(dados)
    if not ok:
        return False, msg

    if produto_id:
        ok = atualizar_produto(produto_id, dados)
        return ok, "Produto atualizado com sucesso!" if ok else "Erro ao atualizar produto."
    else:
        novo_id = inserir_produto(dados)
        return True, f"Produto cadastrado com sucesso! ID: #{novo_id:02d}"


def remover(produto_id: int) -> tuple[bool, str]:
    """Remove (exclusão lógica) um produto."""
    ok = excluir_produto(produto_id)
    return ok, "Produto removido com sucesso!" if ok else "Erro ao remover produto."


# ------------------------------------------------------------------
# Status do estoque
# ------------------------------------------------------------------

def _calcular_status(quantidade: int, estoque_minimo: int) -> str:
    """
    Retorna o status textual do estoque:
    - 'sem_estoque'   → quantidade = 0
    - 'estoque_baixo' → quantidade <= estoque_minimo
    - 'em_estoque'    → dentro do normal
    - 'estoque_alto'  → quantidade >= 3x o mínimo
    """
    if quantidade <= 0:
        return "sem_estoque"
    if quantidade <= estoque_minimo:
        return "estoque_baixo"
    if quantidade >= estoque_minimo * 3:
        return "estoque_alto"
    return "em_estoque"


# ------------------------------------------------------------------
# Validação
# ------------------------------------------------------------------

def _validar(dados: dict) -> tuple[bool, str]:
    """Valida os campos obrigatórios antes de salvar."""
    if not dados.get("nome", "").strip():
        return False, "O campo Nome é obrigatório."

    try:
        preco = float(dados.get("preco", 0))
        if preco < 0:
            raise ValueError
    except (ValueError, TypeError):
        return False, "Preço inválido. Informe um valor numérico positivo."

    try:
        qtd = int(dados.get("quantidade", 0))
        if qtd < 0:
            raise ValueError
    except (ValueError, TypeError):
        return False, "Quantidade inválida. Informe um número inteiro positivo."

    return True, ""
