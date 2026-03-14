"""
relatorios_view.py - Tela de Relatórios (Etapa 6).
Dois cards: Fechamento do Dia e Fechamento do Mês.
Clicar em "Ver" substituirá o bloco por uma tabela detalhada (próxima etapa).
"""

import datetime
import logging
import customtkinter as ctk
from tkinter import messagebox

from database import conectar
from utils import formatar_moeda
from views.despesa_form import DespesaForm
from controllers.despesa_controller import obter_por_id as obter_despesa_por_id

log = logging.getLogger(__name__)

# Meses em português para o seletor do card Mês
_MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Tenta importar tkcalendar para o date picker nativo
try:
    from tkcalendar import DateEntry as _DateEntry
    _TEM_TKCALENDAR = True
except ImportError:
    _TEM_TKCALENDAR = False


# ------------------------------------------------------------------
# Consultas diretas ao banco (sem camada extra de model por enquanto)
# ------------------------------------------------------------------
def _resumo_dia(data_iso: str) -> dict:
    """Retorna qtd de vendas e valor total de um dia (formato AAAA-MM-DD)."""
    conn = conectar()
    row = conn.execute(
        """SELECT COUNT(*) AS qtd, COALESCE(SUM(total_final), 0) AS total
           FROM vendas
           WHERE status = 'concluida'
             AND DATE(criado_em) = ?""",
        (data_iso,),
    ).fetchone()
    conn.close()
    return {"qtd": row[0], "total": float(row[1])}


def _resumo_mes(mes: int, ano: int) -> dict:
    """Retorna qtd de vendas e valor total de um mês/ano."""
    conn = conectar()
    row = conn.execute(
        """SELECT COUNT(*) AS qtd, COALESCE(SUM(total_final), 0) AS total
           FROM vendas
           WHERE status = 'concluida'
             AND strftime('%m', criado_em) = ?
             AND strftime('%Y', criado_em) = ?""",
        (f"{mes:02d}", str(ano)),
    ).fetchone()
    conn.close()
    return {"qtd": row[0], "total": float(row[1])}


# ------------------------------------------------------------------
# View principal
# ------------------------------------------------------------------
class RelatoriosView(ctk.CTkFrame):
    """Tela de Relatórios com cards de Fechamento do Dia e do Mês."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        hoje = datetime.date.today()
        self._data_dia_sel = hoje
        self._mes_sel  = hoje.month
        self._ano_sel  = hoje.year

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        log.info("RelatoriosView carregada.")
        self._construir_ui()

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        # Título da tela
        ctk.CTkLabel(
            self, text="📊  Relatórios",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

        # Container principal (fundo cinza — será trocado pelo bloco de tabela ao clicar Ver)
        self._container = ctk.CTkFrame(self, fg_color="#d8d8d8", corner_radius=12)
        self._container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self._container.grid_columnconfigure((0, 1), weight=1)
        self._container.grid_rowconfigure(1, weight=1)

        self._mostrar_cards()

    # ------------------------------------------------------------------
    # Cards de seleção de período
    # ------------------------------------------------------------------
    def _mostrar_cards(self):
        """Exibe os dois cards de seleção de data no container."""
        for w in self._container.winfo_children():
            w.destroy()

        # Sub-título do container
        ctk.CTkLabel(
            self._container, text="Sistema de Relatório",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        self._construir_card_dia()
        self._construir_card_mes()

    def _construir_card_dia(self):
        """Card esquerdo: Fechamento do Dia."""
        card = ctk.CTkFrame(self._container, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, padx=(14, 7), pady=(0, 14), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Fechamento do Dia",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text=(
                "Visualize todas as vendas do dia com detalhes completos: preços, despesas,\n"
                "histórico de vendas, taxas e possibilidade de exclusão."
            ),
            font=ctk.CTkFont(size=11), text_color="#666666",
            justify="left", anchor="w",
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        # ── Linha do seletor de data + botão Ver ──────────────────
        picker = ctk.CTkFrame(card, fg_color="transparent")
        picker.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="ew")
        picker.grid_columnconfigure(0, weight=1)

        if _TEM_TKCALENDAR:
            self._de_dia = _DateEntry(
                picker, locale="pt_BR", date_pattern="dd/MM/yyyy",
                font=("Segoe UI", 12), width=14,
                background="#1f6aa5", foreground="white",
                headersbackground="#1f6aa5", headersforeground="white",
                selectbackground="#1f6aa5",
            )
            self._de_dia.set_date(self._data_dia_sel)
            self._de_dia.grid(row=0, column=0, padx=(0, 8), ipady=4, sticky="ew")
        else:
            # Fallback: campo de texto simples
            self._entry_dia = ctk.CTkEntry(
                picker, height=34, fg_color="white",
                border_color="#cccccc", font=ctk.CTkFont(size=12),
                placeholder_text="DD/MM/AAAA",
            )
            self._entry_dia.insert(0, self._data_dia_sel.strftime("%d/%m/%Y"))
            self._entry_dia.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            picker, text="🔍  Ver", width=110, height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._ver_dia,
        ).grid(row=0, column=1)

        # ── Separador ─────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1, corner_radius=0).grid(
            row=3, column=0, padx=14, pady=(0, 10), sticky="ew"
        )

        # ── Resumo Rápido do Dia ──────────────────────────────────
        ctk.CTkLabel(
            card, text="Resumo Rápido do Dia",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=4, column=0, padx=16, pady=(0, 6), sticky="w")

        r = _resumo_dia(datetime.date.today().isoformat())
        row_r = ctk.CTkFrame(card, fg_color="transparent")
        row_r.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="w")

        ctk.CTkLabel(
            row_r, text="Total de Vendas: ",
            font=ctk.CTkFont(size=12), text_color="#333333",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text=str(r["qtd"]),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2e7d32",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text="    Valor Total: ",
            font=ctk.CTkFont(size=12), text_color="#333333",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text=formatar_moeda(r["total"]),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2e7d32",
        ).pack(side="left")

    def _construir_card_mes(self):
        """Card direito: Fechamento do Mês."""
        card = ctk.CTkFrame(self._container, fg_color="white", corner_radius=12)
        card.grid(row=1, column=1, padx=(7, 14), pady=(0, 14), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Fechamento do Mês",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            card,
            text=(
                "Relatório mensal consolidado com todas as vendas, preços, despesas, taxas,\n"
                "forma de pagamento e opção de impressão."
            ),
            font=ctk.CTkFont(size=11), text_color="#666666",
            justify="left", anchor="w",
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        # ── Seletor de mês/ano + botão Ver ────────────────────────
        picker = ctk.CTkFrame(card, fg_color="transparent")
        picker.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="ew")
        picker.grid_columnconfigure(0, weight=1)

        mes_ano = ctk.CTkFrame(picker, fg_color="transparent")
        mes_ano.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        mes_ano.grid_columnconfigure(0, weight=1)

        self.opt_mes = ctk.CTkOptionMenu(
            mes_ano, values=_MESES_PT, height=34,
            font=ctk.CTkFont(size=12),
        )
        self.opt_mes.set(_MESES_PT[self._mes_sel - 1])
        self.opt_mes.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.entry_ano = ctk.CTkEntry(
            mes_ano, width=68, height=34,
            fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12),
        )
        self.entry_ano.insert(0, str(self._ano_sel))
        self.entry_ano.grid(row=0, column=1)

        ctk.CTkButton(
            picker, text="🔍  Ver", width=110, height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._ver_mes,
        ).grid(row=0, column=1)

        # ── Separador ─────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1, corner_radius=0).grid(
            row=3, column=0, padx=14, pady=(0, 10), sticky="ew"
        )

        # ── Resumo Rápido do Mês ──────────────────────────────────
        ctk.CTkLabel(
            card, text="Resumo Rápido do Mês",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=4, column=0, padx=16, pady=(0, 6), sticky="w")

        r = _resumo_mes(self._mes_sel, self._ano_sel)
        row_r = ctk.CTkFrame(card, fg_color="transparent")
        row_r.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="w")

        ctk.CTkLabel(
            row_r, text="Total de Vendas: ",
            font=ctk.CTkFont(size=12), text_color="#333333",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text=str(r["qtd"]),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2e7d32",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text="    Valor Total: ",
            font=ctk.CTkFont(size=12), text_color="#333333",
        ).pack(side="left")
        ctk.CTkLabel(
            row_r, text=formatar_moeda(r["total"]),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2e7d32",
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Ações dos botões Ver
    # ------------------------------------------------------------------
    def _ver_dia(self):
        """Exibe o Fechamento do Dia: cards financeiros + tabela cronológica."""
        # ── Resolve data selecionada ──────────────────────────────
        if _TEM_TKCALENDAR:
            data_obj = self._de_dia.get_date()
        else:
            raw = self._entry_dia.get().strip()
            try:
                data_obj = datetime.datetime.strptime(raw, "%d/%m/%Y").date()
            except ValueError:
                messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA.")
                return

        data_iso = data_obj.strftime("%Y-%m-%d")   # para SQLite
        data_br  = data_obj.strftime("%d/%m/%Y")   # para exibição

        # ── Consultas ao banco ────────────────────────────────────
        conn = conectar()

        # Totais por forma de pagamento
        rows_vend = conn.execute(
            """SELECT forma_pagamento,
                      COALESCE(taxa_cartao, 0.0) AS taxa_cartao,
                      total_final,
                      COALESCE(parcelas, 1) AS parcelas
               FROM vendas
               WHERE status = 'concluida'
                 AND DATE(criado_em) = ?""",
            (data_iso,),
        ).fetchall()

        # Despesas do dia (data armazenada como DD/MM/AAAA)
        rows_desp = conn.execute(
            """SELECT id, descricao, responsavel, valor, forma_pagamento, status
               FROM despesas
               WHERE substr(data,7,4) || '-' || substr(data,4,2) || '-' || substr(data,1,2) = ?
               ORDER BY id ASC""",
            (data_iso,),
        ).fetchall()

        # Timeline: itens de venda do dia
        rows_itens = conn.execute(
            """SELECT v.criado_em,
                      COALESCE(v.nome_avulso, c.nome, 'Sem Cadastro') AS nome,
                      p.nome AS prod,
                      iv.quantidade,
                      iv.preco_unitario,
                      iv.subtotal,
                      v.forma_pagamento,
                      COALESCE(v.parcelas, 1) AS parcelas,
                      v.id AS venda_id,
                      iv.id AS item_id
               FROM itens_venda iv
               JOIN vendas v ON v.id = iv.venda_id
               LEFT JOIN clientes c ON c.id = v.cliente_id
               LEFT JOIN produtos p ON p.id = iv.produto_id
               WHERE v.status = 'concluida'
                 AND DATE(v.criado_em) = ?
               ORDER BY v.criado_em ASC""",
            (data_iso,),
        ).fetchall()

        conn.close()

        # ── Calcula totais ────────────────────────────────────────
        tot_dinheiro  = sum(r["total_final"] for r in rows_vend if r["forma_pagamento"] == "dinheiro")
        tot_pix       = sum(r["total_final"] for r in rows_vend if r["forma_pagamento"] == "pix")
        tot_prazo     = sum(r["total_final"] for r in rows_vend if r["forma_pagamento"] == "a_prazo")
        tot_cartao_br = sum(r["total_final"] for r in rows_vend if r["forma_pagamento"] == "cartao")
        tot_cartao_lq = sum(
            r["total_final"] * (1 - r["taxa_cartao"] / 100)
            for r in rows_vend if r["forma_pagamento"] == "cartao"
        )

        desp_pagas = sum(
            r["valor"] for r in rows_desp
            if r["status"] == "pago" and r["forma_pagamento"] == "Dinheiro"
        )
        desp_dia = sum(r["valor"] for r in rows_desp)

        saldo_liq_caixa = tot_dinheiro - desp_pagas
        saldo_total     = tot_dinheiro + tot_cartao_br + tot_pix
        saldo_total_liq = tot_dinheiro + tot_cartao_lq + tot_pix

        # ── Reconstrói o container ────────────────────────────────
        for w in self._container.winfo_children():
            w.destroy()

        # Reseta pesos de linhas/colunas herdados do layout de cards
        for i in range(4):
            self._container.grid_rowconfigure(i, weight=0)
        self._container.grid_columnconfigure(0, weight=1)
        self._container.grid_columnconfigure(1, weight=0)
        self._container.grid_rowconfigure(2, weight=1)

        # ── Cabeçalho ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(self._container, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            hdr, text="← Voltar", width=100, height=32,
            fg_color="#555555", hover_color="#444444",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._mostrar_cards,
        ).grid(row=0, column=0, padx=(0, 12))

        ctk.CTkLabel(
            hdr,
            text=f"Fechamento do Dia  —  {data_br}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            hdr, text="🖨 Imprimir", width=120, height=32,
            fg_color="#1f6aa5", hover_color="#1557a0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: messagebox.showinfo("Em breve", "Impressão será implementada em breve."),
        ).grid(row=0, column=2, padx=(8, 0))

        # ── Separador ── ──────────────────────────────────────────
        ctk.CTkFrame(self._container, fg_color="#cccccc", height=1, corner_radius=0).grid(
            row=1, column=0, padx=16, pady=(4, 0), sticky="ew"
        )

        # ── Área scrollável ───────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self._container, fg_color="#d8d8d8", corner_radius=0)
        scroll.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Subtítulo Resumo ──────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Resumo Financeiro do Dia",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        # ── Cards financeiros ─────────────────────────────────────
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        for c in range(5):
            cards_frame.grid_columnconfigure(c, weight=1)

        def _card(parent, row, col, titulo, valor, cor_valor="#1a1a1a",
                  subtitulo="", cor_bg="white", rowspan=1, colspan=1):
            """Cria um card financeiro padronizado."""
            fr = ctk.CTkFrame(parent, fg_color=cor_bg, corner_radius=10)
            fr.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                    padx=5, pady=5, ipadx=10, ipady=10, sticky="nsew")
            ctk.CTkLabel(
                fr, text=titulo,
                font=ctk.CTkFont(size=11), text_color="#666666", anchor="w",
            ).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(
                fr, text=formatar_moeda(valor),
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=cor_valor, anchor="w",
            ).pack(anchor="w", padx=10)
            if subtitulo:
                ctk.CTkLabel(
                    fr, text=subtitulo,
                    font=ctk.CTkFont(size=9), text_color="#999999", anchor="w",
                ).pack(anchor="w", padx=10, pady=(0, 6))

        # Linha 1
        _card(cards_frame, 0, 0, "💵  Total em Dinheiro", tot_dinheiro, cor_valor="#1a1a1a")
        _card(cards_frame, 0, 1, "💳  Total em Cartão (líquido)", tot_cartao_lq,
              cor_valor="#1a1a1a", subtitulo="Descontado taxa do cartão")
        _card(cards_frame, 0, 2, "📤  Despesas Pagas (Dinheiro)", desp_pagas,
              cor_valor="#555555", subtitulo="Despesas pagas com Dinheiro")
        _card(cards_frame, 0, 3, "🔴  Despesas do Dia (Total)", desp_dia,
              cor_valor="#c62828", subtitulo="Montante de despesas do dia", cor_bg="#fff5f5")

        # Card especial: Adicionar Erro de Caixa
        fr_erro = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
        fr_erro.grid(row=0, column=4, padx=5, pady=5, ipadx=10, ipady=10, sticky="nsew")
        ctk.CTkLabel(
            fr_erro, text="⚠️  Erro de Caixa",
            font=ctk.CTkFont(size=11), text_color="#666666", anchor="w",
        ).pack(anchor="w", padx=10, pady=(10, 4))
        ctk.CTkLabel(
            fr_erro, text="R$ 0,00",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).pack(anchor="w", padx=10)
        ctk.CTkButton(
            fr_erro, text="+ Adicionar", height=28, width=110,
            font=ctk.CTkFont(size=11),
            fg_color="#3a9adf", hover_color="#2e7d32",
            command=lambda: messagebox.showinfo("Em breve", "Funcionalidade em desenvolvimento."),
        ).pack(anchor="w", padx=10, pady=(4, 10))

        # Linha 2
        _card(cards_frame, 1, 0, "📲  Total em PIX", tot_pix, cor_valor="#1a1a1a")
        _card(cards_frame, 1, 1, "📋  Total à Prazo", tot_prazo,
              cor_valor="#7a6000", cor_bg="#fffde7")
        _card(cards_frame, 1, 2, "💰  Saldo Líquido (Caixa)", saldo_liq_caixa,
              cor_valor="#2e7d32", subtitulo="Dinheiro − Despesas Pagas", cor_bg="#f1f8e9")
        _card(cards_frame, 1, 3, "🏦  Saldo Total", saldo_total,
              cor_valor="#7a6000", subtitulo="Dinheiro + Cartão + PIX", cor_bg="#fffde7")

        # Saldo Total Líquido — card grande, destaque verde
        fr_liq = ctk.CTkFrame(cards_frame, fg_color="#2e7d32", corner_radius=10)
        fr_liq.grid(row=1, column=4, padx=5, pady=5, ipadx=14, ipady=14, sticky="nsew")
        ctk.CTkLabel(
            fr_liq, text="✅  Saldo Total (Líquido)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#c8e6c9", anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(
            fr_liq, text=formatar_moeda(saldo_total_liq),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white", anchor="w",
        ).pack(anchor="w", padx=14)
        ctk.CTkLabel(
            fr_liq, text="Dinheiro + Cartão + PIX − Taxas",
            font=ctk.CTkFont(size=9), text_color="#a5d6a7", anchor="w",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # ── Subtítulo Tabela ──────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Histórico do Dia",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=2, column=0, padx=16, pady=(10, 4), sticky="w")

        # ── Tabela cronológica ────────────────────────────────────
        tbl_frame = ctk.CTkFrame(scroll, fg_color="white", corner_radius=10)
        tbl_frame.grid(row=3, column=0, padx=16, pady=(0, 20), sticky="ew")

        cols = ["Data/Hora", "Nome", "Produto", "Qtd.", "Preço", "Total", "Pagamento", "Ações"]
        pesos = [14, 16, 20, 5, 10, 10, 14, 6]
        for ci, (c_txt, peso) in enumerate(zip(cols, pesos)):
            tbl_frame.grid_columnconfigure(ci, weight=peso)
            ctk.CTkLabel(
                tbl_frame, text=c_txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#1f6aa5", anchor="w",
            ).grid(row=0, column=ci, padx=8, pady=(8, 4), sticky="w")

        # Separador cabeçalho
        ctk.CTkFrame(tbl_frame, fg_color="#e0e0e0", height=1, corner_radius=0).grid(
            row=1, column=0, columnspan=8, padx=6, pady=0, sticky="ew"
        )

        # ── Monta linhas mesclando vendas e despesas ──────────────
        # Converte itens de venda para lista de dicts normalizados
        linhas: list[dict] = []
        for r in rows_itens:
            hora = r["criado_em"][11:16] if r["criado_em"] and len(r["criado_em"]) >= 16 else "--"
            fp = r["forma_pagamento"]
            if fp == "cartao" and r["parcelas"] > 1:
                fp_label = f"Cartão ({r['parcelas']}x)"
            elif fp == "cartao":
                fp_label = "Cartão"
            elif fp == "dinheiro":
                fp_label = "Dinheiro"
            elif fp == "pix":
                fp_label = "PIX"
            elif fp == "a_prazo":
                fp_label = "A Prazo"
            else:
                fp_label = fp
            linhas.append({
                "hora": hora,
                "nome": r["nome"],
                "prod": r["prod"] or "—",
                "qtd": str(int(r["quantidade"])) if r["quantidade"] else "1",
                "preco": formatar_moeda(r["preco_unitario"]),
                "total": formatar_moeda(r["subtotal"]),
                "pag": fp_label,
                "tipo": "venda",
                "ref_id": r["item_id"],
                "cor": "#1a1a1a",
            })

        for rd in rows_desp:
            linhas.append({
                "hora": "—",
                "nome": rd["responsavel"] or rd["descricao"],
                "prod": rd["descricao"],
                "qtd": "#",
                "preco": "#",
                "total": formatar_moeda(rd["valor"]),
                "pag": rd["forma_pagamento"],
                "tipo": "despesa",
                "ref_id": rd["id"],
                "cor": "#c62828",
            })

        if not linhas:
            ctk.CTkLabel(
                tbl_frame, text="Nenhum registro encontrado para este dia.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=2, column=0, columnspan=8, padx=8, pady=20)
        else:
            for li, linha in enumerate(linhas):
                tr = li + 2  # linha da tabela (0=cabeçalho, 1=sep)
                cor = linha["cor"]
                bg_row = "#fff8f8" if linha["tipo"] == "despesa" else "white"

                vals = [
                    linha["hora"],
                    linha["nome"],
                    linha["prod"],
                    linha["qtd"],
                    linha["preco"],
                    linha["total"],
                    linha["pag"],
                ]
                for ci, v in enumerate(vals):
                    ctk.CTkLabel(
                        tbl_frame, text=v,
                        font=ctk.CTkFont(size=11),
                        text_color=cor,
                        fg_color=bg_row,
                        anchor="w",
                    ).grid(row=tr, column=ci, padx=8, pady=3, sticky="ew")

                # Coluna Ações
                acoes_fr = ctk.CTkFrame(tbl_frame, fg_color=bg_row)
                acoes_fr.grid(row=tr, column=7, padx=4, pady=2, sticky="ew")

                def _editar(tipo=linha["tipo"], ref=linha["ref_id"], data_i=data_iso, data_b=data_br):
                    self._editar_registro(tipo, ref, data_i, data_b)

                def _excluir(tipo=linha["tipo"], ref=linha["ref_id"], data_i=data_iso, data_b=data_br):
                    self._excluir_registro(tipo, ref, data_i, data_b)

                ctk.CTkButton(
                    acoes_fr, text="✏️", width=30, height=24,
                    fg_color="transparent", text_color="#000000",
                    hover_color="#e0e0e0",
                    font=ctk.CTkFont(size=13),
                    command=_editar,
                ).pack(side="left")

                ctk.CTkButton(
                    acoes_fr, text="🗑", width=30, height=24,
                    fg_color="transparent", text_color="#c62828",
                    hover_color="#ffebee",
                    font=ctk.CTkFont(size=13),
                    command=_excluir,
                ).pack(side="left")

    # ------------------------------------------------------------------
    # Edição de registro a partir do histórico
    # ------------------------------------------------------------------
    def _editar_registro(self, tipo: str, ref_id: int, data_iso: str, data_br: str):
        """Abre formulário de edição para item de venda ou despesa."""
        if tipo == "despesa":
            despesa = obter_despesa_por_id(ref_id)
            if not despesa:
                messagebox.showerror("Erro", "Despesa não encontrada.")
                return

            def _ao_salvar():
                self._recarregar_dia(data_iso, data_br)

            DespesaForm(self, despesa, _ao_salvar)

        elif tipo == "venda":
            # Popup simples para editar quantidade e preço do item de venda
            conn = conectar()
            item = conn.execute(
                "SELECT produto_id, quantidade, preco_unitario FROM itens_venda WHERE id = ?",
                (ref_id,),
            ).fetchone()
            conn.close()
            if not item:
                messagebox.showerror("Erro", "Item não encontrado.")
                return

            popup = ctk.CTkToplevel(self)
            popup.title("Editar Item de Venda")
            popup.geometry("320x240")
            popup.resizable(False, False)
            popup.grab_set()

            ctk.CTkLabel(popup, text="Editar Item de Venda",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(16, 10))

            fr = ctk.CTkFrame(popup, fg_color="transparent")
            fr.pack(padx=20, fill="x")

            ctk.CTkLabel(fr, text="Quantidade:", anchor="w").grid(row=0, column=0, pady=6, sticky="w")
            entry_qtd = ctk.CTkEntry(fr, width=120)
            entry_qtd.insert(0, str(int(item["quantidade"])))
            entry_qtd.grid(row=0, column=1, padx=(8, 0))

            ctk.CTkLabel(fr, text="Preço unitário (R$):", anchor="w").grid(row=1, column=0, pady=6, sticky="w")
            entry_preco = ctk.CTkEntry(fr, width=120)
            entry_preco.insert(0, f"{item['preco_unitario']:.2f}".replace(".", ","))
            entry_preco.grid(row=1, column=1, padx=(8, 0))

            def _salvar_item():
                try:
                    qtd   = int(entry_qtd.get().strip())
                    preco = float(entry_preco.get().strip().replace(",", "."))
                    if qtd <= 0 or preco < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Valor inválido", "Informe quantidade (inteiro > 0) e preço válido.", parent=popup)
                    return

                subtotal = round(qtd * preco, 2)
                conn2 = conectar()
                conn2.execute(
                    "UPDATE itens_venda SET quantidade=?, preco_unitario=?, subtotal=? WHERE id=?",
                    (qtd, preco, subtotal, ref_id),
                )
                conn2.commit()
                conn2.close()
                popup.destroy()
                self._recarregar_dia(data_iso, data_br)

            ctk.CTkButton(
                popup, text="💾 Salvar", height=36,
                fg_color="#2e7d32", hover_color="#1b5e20",
                command=_salvar_item,
            ).pack(pady=(16, 0), padx=20, fill="x")

    # ------------------------------------------------------------------
    # Recarga do fechamento do dia (usada após editar/excluir)
    # ------------------------------------------------------------------
    def _recarregar_dia(self, data_iso: str, data_br: str):
        """Reposiciona o date picker e recarrega o Fechamento do Dia."""
        data_obj = datetime.datetime.strptime(data_br, "%d/%m/%Y").date()
        if _TEM_TKCALENDAR:
            self._de_dia.set_date(data_obj)
        else:
            self._entry_dia.delete(0, "end")
            self._entry_dia.insert(0, data_br)
        self._ver_dia()

    # ------------------------------------------------------------------
    # Exclusão de registro a partir do histórico
    # ------------------------------------------------------------------
    def _excluir_registro(self, tipo: str, ref_id: int, data_iso: str, data_br: str):
        """Exclui um item de venda ou despesa e recarrega o fechamento do dia."""
        if tipo == "venda":
            confirmar = messagebox.askyesno(
                "Excluir Item",
                "Deseja realmente excluir este item da venda?\n"
                "O produto voltará ao estoque.",
            )
            if not confirmar:
                return
            conn = conectar()
            # Restaura estoque antes de excluir
            item = conn.execute(
                "SELECT produto_id, quantidade FROM itens_venda WHERE id = ?", (ref_id,)
            ).fetchone()
            if item:
                conn.execute(
                    "UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
                conn.execute("DELETE FROM itens_venda WHERE id = ?", (ref_id,))
                conn.commit()
            conn.close()

        elif tipo == "despesa":
            confirmar = messagebox.askyesno(
                "Excluir Despesa",
                "Deseja realmente excluir esta despesa?",
            )
            if not confirmar:
                return
            conn = conectar()
            conn.execute("DELETE FROM despesas WHERE id = ?", (ref_id,))
            conn.commit()
            conn.close()

        # Recarrega o fechamento do dia
        self._recarregar_dia(data_iso, data_br)

    def _ver_mes(self):
        """Substituirá o container pela tabela detalhada do mês (próxima etapa)."""
        mes_nome = self.opt_mes.get()
        ano_str  = self.entry_ano.get().strip()

        # TODO: substituir cards pela tabela detalhada (próxima etapa)
        messagebox.showinfo(
            "Em breve",
            f"A tabela detalhada de {mes_nome}/{ano_str} será implementada na próxima etapa.",
        )
