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
        """Substituirá o container pela tabela detalhada do dia (próxima etapa)."""
        if _TEM_TKCALENDAR:
            data_str = self._de_dia.get_date().strftime("%d/%m/%Y")
        else:
            data_str = self._entry_dia.get().strip()

        # TODO: substituir cards pela tabela detalhada (próxima etapa)
        messagebox.showinfo(
            "Em breve",
            f"A tabela detalhada do dia {data_str} será implementada na próxima etapa.",
        )

    def _ver_mes(self):
        """Substituirá o container pela tabela detalhada do mês (próxima etapa)."""
        mes_nome = self.opt_mes.get()
        ano_str  = self.entry_ano.get().strip()

        # TODO: substituir cards pela tabela detalhada (próxima etapa)
        messagebox.showinfo(
            "Em breve",
            f"A tabela detalhada de {mes_nome}/{ano_str} será implementada na próxima etapa.",
        )
