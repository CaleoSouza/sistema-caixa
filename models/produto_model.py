"""
produto_model.py - Consultas ao banco de dados para a entidade Produto.
Toda comunicação direta com o SQLite referente a produtos fica aqui.
"""

from database import conectar


# ------------------------------------------------------------------
# Leitura
# ------------------------------------------------------------------

def listar_estoque_baixo() -> list:
    """Retorna produtos ativos com estoque crítico: sem estoque (0) ou baixo (1 a 4)."""
    conn = conectar()
    rows = conn.execute(
        """SELECT id, nome, categoria, fornecedor, preco, preco_custo,
                  quantidade, estoque_minimo, codigo_barras,
                  data_validade, imagem
           FROM produtos
           WHERE ativo = 1 AND quantidade <= 4
           ORDER BY quantidade ASC""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_proximos_vencer() -> list:
    """Retorna produtos ativos com data_validade válida, já vencidos ou vencendo nos próximos 30 dias."""
    conn = conectar()
    rows = conn.execute(
        """SELECT id, nome, categoria, fornecedor, preco, preco_custo,
                  quantidade, estoque_minimo, codigo_barras,
                  data_validade, imagem
           FROM produtos
           WHERE ativo = 1
             AND data_validade IS NOT NULL
             AND data_validade != ''
             AND date(data_validade) <= date('now', '+30 days')
           ORDER BY data_validade ASC""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_produtos(busca: str = "") -> list:
    """
    Retorna lista de produtos ativos.
    Se 'busca' for informado, filtra por nome, categoria ou código de barras.
    """
    conn = conectar()
    if busca:
        termo = f"%{busca}%"
        rows = conn.execute(
            """SELECT id, nome, categoria, fornecedor, preco, preco_custo,
                      quantidade, estoque_minimo, codigo_barras,
                      data_validade, imagem
               FROM produtos
               WHERE ativo = 1
                 AND (nome LIKE ? OR categoria LIKE ? OR codigo_barras LIKE ?
                      OR fornecedor LIKE ?)
               ORDER BY nome""",
            (termo, termo, termo, termo),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, nome, categoria, fornecedor, preco, preco_custo,
                      quantidade, estoque_minimo, codigo_barras,
                      data_validade, imagem
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

    # Estoque crítico = sem estoque (0) + baixo estoque (1 a 4)
    estoque_baixo = conn.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo = 1 AND quantidade <= 4"
    ).fetchone()[0]

    # Produtos já vencidos ou com validade nos próximos 30 dias
    proximos_vencer = conn.execute(
        """SELECT COUNT(*) FROM produtos
           WHERE ativo = 1
             AND data_validade IS NOT NULL
             AND data_validade != ''
             AND date(data_validade) <= date('now', '+30 days')"""
    ).fetchone()[0]

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

def codigo_barras_existe(codigo: str, excluir_id: int = None) -> bool:
    """
    Verifica se um código de barras já está cadastrado.
    Se 'excluir_id' for informado, ignora o próprio produto (para edição).
    """
    conn = conectar()
    if excluir_id:
        row = conn.execute(
            "SELECT id FROM produtos WHERE codigo_barras = ? AND id != ? AND ativo = 1",
            (codigo, excluir_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM produtos WHERE codigo_barras = ? AND ativo = 1",
            (codigo,),
        ).fetchone()
    conn.close()
    return row is not None


def inserir_produto(dados: dict) -> int:
    """Insere um novo produto e retorna o ID gerado."""
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO produtos
               (nome, descricao, categoria, fornecedor, preco, preco_custo,
                quantidade, estoque_minimo, codigo_barras, data_validade,
                imagem, imagem2, imagem3)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            dados.get("nome", ""),
            dados.get("descricao", ""),
            dados.get("categoria", ""),
            dados.get("fornecedor", "") or None,
            dados.get("preco", 0.0),
            dados.get("preco_custo", 0.0),
            dados.get("quantidade", 0),
            dados.get("estoque_minimo", 5),
            dados.get("codigo_barras") or None,
            dados.get("data_validade") or None,
            dados.get("imagem") or None,
            dados.get("imagem2") or None,
            dados.get("imagem3") or None,
        ),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def atualizar_produto(produto_id: int, dados: dict) -> bool:
    """Atualiza os dados de um produto existente."""
    conn = conectar()
    cursor = conn.execute(
        """UPDATE produtos SET
               nome = ?, descricao = ?, categoria = ?, fornecedor = ?,
               preco = ?, preco_custo = ?, quantidade = ?, estoque_minimo = ?,
               codigo_barras = ?, data_validade = ?,
               imagem = ?, imagem2 = ?, imagem3 = ?,
               atualizado_em = datetime('now','localtime')
           WHERE id = ? AND ativo = 1""",
        (
            dados.get("nome", ""),
            dados.get("descricao", ""),
            dados.get("categoria", ""),
            dados.get("fornecedor", "") or None,
            dados.get("preco", 0.0),
            dados.get("preco_custo", 0.0),
            dados.get("quantidade", 0),
            dados.get("estoque_minimo", 5),
            dados.get("codigo_barras") or None,
            dados.get("data_validade") or None,
            dados.get("imagem") or None,
            dados.get("imagem2") or None,
            dados.get("imagem3") or None,
            produto_id,
        ),
    )
    conn.commit()
    alterado = cursor.rowcount > 0
    conn.close()
    return alterado


def excluir_produto(produto_id: int) -> bool:
    """Exclusão lógica: marca o produto como inativo (ativo = 0)."""
    conn = conectar()
    cursor = conn.execute(
        "UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,)
    )
    conn.commit()
    alterado = cursor.rowcount > 0
    conn.close()
    return alterado


def atualizar_estoque(produto_id: int, quantidade: int) -> bool:
    """Atualiza apenas o estoque de um produto (usado pelo carrinho)."""
    conn = conectar()
    cursor = conn.execute(
        """UPDATE produtos SET quantidade = ?,
               atualizado_em = datetime('now','localtime')
           WHERE id = ? AND ativo = 1""",
        (quantidade, produto_id),
    )
    conn.commit()
    alterado = cursor.rowcount > 0
    conn.close()
    return alterado
