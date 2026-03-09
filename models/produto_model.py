"""
produto_model.py - Consultas ao banco de dados para a entidade Produto.
Toda comunicação direta com o SQLite referente a produtos fica aqui.
"""

from database import conectar


# ------------------------------------------------------------------
# Leitura
# ------------------------------------------------------------------

def listar_produtos(busca: str = "") -> list:
    """
    Retorna lista de produtos ativos.
    Se 'busca' for informado, filtra por nome, categoria ou código de barras.
    """
    conn = conectar()
    if busca:
        termo = f"%{busca}%"
        rows = conn.execute(
            """SELECT id, nome, categoria, preco, preco_custo, quantidade,
                      estoque_minimo, codigo_barras, imagem
               FROM produtos
               WHERE ativo = 1
                 AND (nome LIKE ? OR categoria LIKE ? OR codigo_barras LIKE ?)
               ORDER BY nome""",
            (termo, termo, termo),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, nome, categoria, preco, preco_custo, quantidade,
                      estoque_minimo, codigo_barras, imagem
               FROM produtos
               WHERE ativo = 1
               ORDER BY nome""",
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_por_id(produto_id: int) -> dict | None:
    """Retorna um produto pelo ID ou None se não encontrado."""
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_por_codigo_barras(codigo: str) -> dict | None:
    """Retorna um produto pelo código de barras."""
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM produtos WHERE codigo_barras = ? AND ativo = 1", (codigo,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------------------
# Resumo para os cards da tela
# ------------------------------------------------------------------

def resumo_produtos() -> dict:
    """
    Retorna estatísticas para os 5 cards da tela de produtos:
    total, itens_em_estoque, valor_total, estoque_baixo, proximos_vencer.
    """
    conn = conectar()

    total = conn.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo = 1"
    ).fetchone()[0]

    itens_estoque = conn.execute(
        "SELECT COALESCE(SUM(quantidade), 0) FROM produtos WHERE ativo = 1"
    ).fetchone()[0]

    valor_total = conn.execute(
        "SELECT COALESCE(SUM(preco * quantidade), 0) FROM produtos WHERE ativo = 1"
    ).fetchone()[0]

    estoque_baixo = conn.execute(
        """SELECT COUNT(*) FROM produtos
           WHERE ativo = 1 AND quantidade > 0 AND quantidade <= estoque_minimo"""
    ).fetchone()[0]

    # "Próximo a vencer" — campo disponível para futura implementação de validade
    # Por enquanto retorna 0 pois a tabela não tem campo de validade ainda
    proximos_vencer = 0

    conn.close()
    return {
        "total":           total,
        "itens_estoque":   int(itens_estoque),
        "valor_total":     float(valor_total),
        "estoque_baixo":   estoque_baixo,
        "proximos_vencer": proximos_vencer,
    }


# ------------------------------------------------------------------
# Escrita
# ------------------------------------------------------------------

def inserir_produto(dados: dict) -> int:
    """Insere um novo produto e retorna o ID gerado."""
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO produtos
               (nome, descricao, categoria, preco, preco_custo,
                quantidade, estoque_minimo, codigo_barras, imagem)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            dados.get("nome", ""),
            dados.get("descricao", ""),
            dados.get("categoria", ""),
            dados.get("preco", 0.0),
            dados.get("preco_custo", 0.0),
            dados.get("quantidade", 0),
            dados.get("estoque_minimo", 5),
            dados.get("codigo_barras") or None,
            dados.get("imagem") or None,
        ),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def atualizar_produto(produto_id: int, dados: dict) -> bool:
    """Atualiza os dados de um produto existente."""
    conn = conectar()
    conn.execute(
        """UPDATE produtos SET
               nome = ?, descricao = ?, categoria = ?, preco = ?, preco_custo = ?,
               quantidade = ?, estoque_minimo = ?, codigo_barras = ?, imagem = ?,
               atualizado_em = datetime('now','localtime')
           WHERE id = ? AND ativo = 1""",
        (
            dados.get("nome", ""),
            dados.get("descricao", ""),
            dados.get("categoria", ""),
            dados.get("preco", 0.0),
            dados.get("preco_custo", 0.0),
            dados.get("quantidade", 0),
            dados.get("estoque_minimo", 5),
            dados.get("codigo_barras") or None,
            dados.get("imagem") or None,
            produto_id,
        ),
    )
    conn.commit()
    alterado = conn.total_changes > 0
    conn.close()
    return alterado


def excluir_produto(produto_id: int) -> bool:
    """Exclusão lógica: marca o produto como inativo (ativo = 0)."""
    conn = conectar()
    conn.execute(
        "UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,)
    )
    conn.commit()
    alterado = conn.total_changes > 0
    conn.close()
    return alterado


def atualizar_estoque(produto_id: int, quantidade: int) -> bool:
    """Atualiza apenas o estoque de um produto (usado pelo carrinho)."""
    conn = conectar()
    conn.execute(
        """UPDATE produtos SET quantidade = ?,
               atualizado_em = datetime('now','localtime')
           WHERE id = ? AND ativo = 1""",
        (quantidade, produto_id),
    )
    conn.commit()
    alterado = conn.total_changes > 0
    conn.close()
    return alterado
