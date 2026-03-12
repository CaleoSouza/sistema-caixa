"""
venda_model.py - Consultas ao banco de dados para Vendas e Itens de Venda.
Toda comunicação direta com o SQLite referente a vendas fica aqui.
"""

from database import conectar


# ------------------------------------------------------------------
# Escrita
# ------------------------------------------------------------------

def registrar_venda(dados: dict, itens: list) -> int:
    """
    Insere um cabeçalho de venda e seus itens no banco.

    dados: {
        cliente_id, total, desconto, total_final,
        forma_pagamento, taxa_cartao, parcelas
    }
    itens: list de { produto_id, quantidade, preco_unitario, subtotal }

    Retorna o id da venda criada.
    """
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO vendas
               (cliente_id, total, desconto, total_final,
                forma_pagamento, taxa_cartao, parcelas)
           VALUES
               (:cliente_id, :total, :desconto, :total_final,
                :forma_pagamento, :taxa_cartao, :parcelas)""",
        dados,
    )
    venda_id = cursor.lastrowid

    for item in itens:
        conn.execute(
            """INSERT INTO itens_venda
                   (venda_id, produto_id, quantidade, preco_unitario, subtotal)
               VALUES (?, ?, ?, ?, ?)""",
            (
                venda_id,
                item["produto_id"],
                item["quantidade"],
                item["preco_unitario"],
                item["subtotal"],
            ),
        )

    conn.commit()
    conn.close()
    return venda_id


# ------------------------------------------------------------------
# Leitura
# ------------------------------------------------------------------

def listar_vendas(limite: int = 100) -> list:
    """Retorna as últimas vendas registradas, unidas com nome do cliente."""
    conn = conectar()
    rows = conn.execute(
        """SELECT v.id, v.cliente_id,
                  COALESCE(c.nome, 'Sem Cadastro') AS cliente_nome,
                  v.total, v.desconto, v.total_final,
                  v.forma_pagamento, v.taxa_cartao, v.parcelas,
                  v.status, v.criado_em
           FROM vendas v
           LEFT JOIN clientes c ON c.id = v.cliente_id
           ORDER BY v.criado_em DESC
           LIMIT ?""",
        (limite,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_itens_venda(venda_id: int) -> list:
    """Retorna os itens detalhados de uma venda."""
    conn = conectar()
    rows = conn.execute(
        """SELECT iv.id, iv.produto_id,
                  COALESCE(p.nome, '—') AS produto_nome,
                  iv.quantidade, iv.preco_unitario, iv.subtotal
           FROM itens_venda iv
           LEFT JOIN produtos p ON p.id = iv.produto_id
           WHERE iv.venda_id = ?""",
        (venda_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def total_vendas_hoje() -> float:
    """Retorna o valor total das vendas concluídas no dia de hoje."""
    conn = conectar()
    result = conn.execute(
        """SELECT COALESCE(SUM(total_final), 0)
           FROM vendas
           WHERE status = 'concluida'
             AND DATE(criado_em) = DATE('now', 'localtime')"""
    ).fetchone()[0]
    conn.close()
    return float(result)


def quantidade_vendas_hoje() -> int:
    """Retorna a quantidade de vendas concluídas no dia de hoje."""
    conn = conectar()
    result = conn.execute(
        """SELECT COUNT(*)
           FROM vendas
           WHERE status = 'concluida'
             AND DATE(criado_em) = DATE('now', 'localtime')"""
    ).fetchone()[0]
    conn.close()
    return int(result)
