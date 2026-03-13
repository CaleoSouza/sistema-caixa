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


# ==================================================================
# Despesas Automáticas (fixas mensais)
# ==================================================================

def listar_despesas_auto() -> list[dict]:
    """Retorna todas as despesas automáticas cadastradas."""
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM despesas_automaticas ORDER BY descricao"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_auto_por_id(auto_id: int) -> dict | None:
    """Retorna uma despesa automática pelo ID."""
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM despesas_automaticas WHERE id = ?", (auto_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def inserir_despesa_auto(dados: dict) -> int:
    """Insere uma nova despesa automática e retorna o ID gerado."""
    conn = conectar()
    cursor = conn.execute("""
        INSERT INTO despesas_automaticas (descricao, dia_mes, responsavel, valor, forma_pagamento)
        VALUES (:descricao, :dia_mes, :responsavel, :valor, :forma_pagamento)
    """, dados)
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def atualizar_despesa_auto(auto_id: int, dados: dict):
    """Atualiza uma despesa automática existente."""
    conn = conectar()
    conn.execute("""
        UPDATE despesas_automaticas
        SET descricao       = :descricao,
            dia_mes         = :dia_mes,
            responsavel     = :responsavel,
            valor           = :valor,
            forma_pagamento = :forma_pagamento
        WHERE id = :id
    """, {**dados, "id": auto_id})
    conn.commit()
    conn.close()


def excluir_despesa_auto(auto_id: int):
    """Remove permanentemente uma despesa automática."""
    conn = conectar()
    conn.execute("DELETE FROM despesas_automaticas WHERE id = ?", (auto_id,))
    conn.commit()
    conn.close()


def gerar_despesas_mes(mes: int, ano: int) -> int:
    """
    Gera despesas na tabela 'despesas' para cada despesa automática
    que ainda não foi inserida no mês/ano informado.
    Retorna a quantidade de despesas criadas.
    """
    import calendar
    automaticas = listar_despesas_auto()
    if not automaticas:
        return 0

    conn = conectar()
    criadas = 0

    # Máximo de dias do mês (evita dia 31 em meses com menos dias)
    max_dias = calendar.monthrange(ano, mes)[1]

    for auto in automaticas:
        # Verifica se já foi gerada neste mês/ano
        ja_existe = conn.execute("""
            SELECT 1 FROM despesas
            WHERE auto_origem_id = ?
              AND substr(data, 4, 2) = ?
              AND substr(data, 7, 4) = ?
        """, (auto["id"], f"{mes:02d}", str(ano))).fetchone()

        if ja_existe:
            continue

        # Ajusta dia para não ultrapassar o limite do mês
        dia = min(auto["dia_mes"], max_dias)
        data_str = f"{dia:02d}/{mes:02d}/{ano}"

        conn.execute("""
            INSERT INTO despesas
                (descricao, data, responsavel, valor, forma_pagamento, status, auto_origem_id)
            VALUES (?, ?, ?, ?, ?, 'agendado', ?)
        """, (
            auto["descricao"],
            data_str,
            auto.get("responsavel") or "",
            auto["valor"],
            auto["forma_pagamento"],
            auto["id"],
        ))
        criadas += 1

    conn.commit()
    conn.close()
    return criadas


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
