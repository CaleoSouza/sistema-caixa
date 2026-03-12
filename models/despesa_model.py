"""
despesa_model.py - Consultas ao banco de dados para a tabela despesas.
"""

from database import conectar


def listar_despesas(busca: str = "", mes: int = 0, ano: int = 0, status: str = "") -> list[dict]:
    """
    Retorna lista de despesas com filtros opcionais.
    - busca: texto livre (descrição, responsável, forma_pagamento)
    - mes/ano: filtra pelo mês e ano (0 = todos)
    - status: 'pago' | 'agendado' | 'em_aberto' | '' (todos)
    """
    conn = conectar()
    params = []
    where = ["1=1"]

    if busca:
        where.append("(descricao LIKE ? OR responsavel LIKE ? OR forma_pagamento LIKE ?)")
        like = f"%{busca}%"
        params += [like, like, like]

    if mes and ano:
        # Data armazenada como DD/MM/AAAA
        where.append("substr(data, 4, 2) = ? AND substr(data, 7, 4) = ?")
        params += [f"{mes:02d}", str(ano)]

    if status:
        where.append("status = ?")
        params.append(status)

    sql = f"""
        SELECT id, descricao, data, responsavel, valor, forma_pagamento, status
        FROM despesas
        WHERE {' AND '.join(where)}
        ORDER BY substr(data,7,4) DESC, substr(data,4,2) DESC, substr(data,1,2) DESC
    """
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_por_id(despesa_id: int) -> dict | None:
    """Retorna uma despesa pelo ID, ou None se não encontrada."""
    conn = conectar()
    row = conn.execute("SELECT * FROM despesas WHERE id = ?", (despesa_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def inserir_despesa(dados: dict) -> int:
    """Insere uma nova despesa e retorna o ID gerado."""
    conn = conectar()
    cursor = conn.execute("""
        INSERT INTO despesas (descricao, data, responsavel, valor, forma_pagamento, status)
        VALUES (:descricao, :data, :responsavel, :valor, :forma_pagamento, :status)
    """, dados)
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def atualizar_despesa(despesa_id: int, dados: dict):
    """Atualiza os campos de uma despesa existente."""
    conn = conectar()
    conn.execute("""
        UPDATE despesas
        SET descricao = :descricao,
            data = :data,
            responsavel = :responsavel,
            valor = :valor,
            forma_pagamento = :forma_pagamento,
            status = :status
        WHERE id = :id
    """, {**dados, "id": despesa_id})
    conn.commit()
    conn.close()


def excluir_despesa(despesa_id: int):
    """Remove permanentemente uma despesa do banco."""
    conn = conectar()
    conn.execute("DELETE FROM despesas WHERE id = ?", (despesa_id,))
    conn.commit()
    conn.close()


def resumo_por_mes(mes: int, ano: int) -> dict:
    """
    Retorna totais agrupados por status para um determinado mês/ano.
    Retorna: {total_mes, total_agendado, total_em_aberto, total_pago}
    """
    conn = conectar()
    sql = """
        SELECT status, SUM(valor) as soma
        FROM despesas
        WHERE substr(data, 4, 2) = ? AND substr(data, 7, 4) = ?
        GROUP BY status
    """
    rows = conn.execute(sql, (f"{mes:02d}", str(ano))).fetchall()
    conn.close()

    totais = {"pago": 0.0, "agendado": 0.0, "em_aberto": 0.0}
    for r in rows:
        if r["status"] in totais:
            totais[r["status"]] = r["soma"] or 0.0

    return {
        "total_mes":       sum(totais.values()),
        "total_agendado":  totais["agendado"],
        "total_em_aberto": totais["em_aberto"],
        "total_pago":      totais["pago"],
    }
