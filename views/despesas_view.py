"""
despesas_view.py - Tela de Gestão de Despesas (Etapa 5).
Layout: painel esquerdo com tabela + filtros; painel direito com 4 cards de totais.
"""

import datetime
import logging
import customtkinter as ctk
from tkinter import messagebox

from controllers.despesa_controller import (
    obter_lista, obter_resumo, remover, STATUS_LABELS,
    obter_lista_auto, remover_auto, obter_auto_por_id,
    gerar_despesas_mes_atual,
)
from views.despesa_form import DespesaForm
from views.despesa_auto_form import DespesaAutoForm
from utils import formatar_moeda

log = logging.getLogger(__name__)

# Meses em português
_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Colunas da tabela: (rótulo, peso)
COLUNAS = [
    ("Descrição",    5),
    ("Data",         2),
    ("Responsável",  3),
    ("Valor",        2),
    ("Pagamento",    2),
    ("Status",       2),
    ("Ações",        0),   # largura fixa via minsize
]

# Cores por status
_STATUS_COR = {
    "pago":      "#2e7d32",
    "agendado":  "#d97706",
    "em_aberto": "#e53935",
}


class DespesasView(ctk.CTkFrame):
    """Tela de Controle de Despesas."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        hoje = datetime.date.today()
        self._mes_tabela  = hoje.month
        self._ano_tabela  = hoje.year
        self._status_filtro = ""      # '' = todos

        # Mês dos cards (cada card tem seletor independente)
        self._mes_card = {
            "total_mes":       hoje.month,
            "total_agendado":  hoje.month,
            "total_em_aberto": hoje.month,
            "total_pago":      hoje.month,
        }
        self._ano_card = hoje.year

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        log.info("DespesasView carregada.")
        # Gera despesas automáticas do mês atual ao abrir a tela
        criadas = gerar_despesas_mes_atual()
        if criadas:
            log.info("Despesas automáticas geradas: %d", criadas)
        self._construir_ui()

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        # ── Cabeçalho ──────────────────────────────────────────────
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.grid(row=0, column=0, columnspan=2, padx=20, pady=(18, 6), sticky="ew")
        cab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cab, text="💸  Despesas",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            cab, text="+ Adicionar Nova Despesa", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._nova_despesa,
        ).grid(row=0, column=1, sticky="e")

        # ── Painel esquerdo ─────────────────────────────────────────
        self._criar_painel_esquerdo()

        # ── Painel direito (cards) ──────────────────────────────────
        self._criar_painel_direito()

    # ------------------------------------------------------------------
    # Painel esquerdo: tabela + filtros
    # ------------------------------------------------------------------
    def _criar_painel_esquerdo(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        # ── Barra de filtros ──────────────────────────────────────
        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        barra.grid_columnconfigure(0, weight=1)

        # Título + botão Imprimir na mesma linha
        tit_row = ctk.CTkFrame(barra, fg_color="transparent")
        tit_row.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        tit_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tit_row, text="Controle de Despesas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            tit_row, text="🖨️  Imprimir Despesas", height=32, width=170,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._imprimir,
        ).grid(row=0, column=1, sticky="e")

        # Busca
        self.entry_busca = ctk.CTkEntry(
            barra, height=34, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12),
            placeholder_text="Descrição, categoria, responsável...",
        )
        self.entry_busca.grid(row=1, column=0, padx=(0, 8), sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._carregar_tabela())

        ctk.CTkButton(
            barra, text="🔍 Buscar", width=90, height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._carregar_tabela,
        ).grid(row=1, column=1, padx=(0, 8))

        # Dropdown de mês
        self.opt_mes = ctk.CTkOptionMenu(
            barra, values=_MESES, width=120, height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._mudar_mes_tabela,
        )
        self.opt_mes.set(_MESES[self._mes_tabela - 1])
        self.opt_mes.grid(row=1, column=2, padx=(0, 8))

        # Dropdown de status
        status_opcoes = ["Todos"] + list(STATUS_LABELS.values())
        self.opt_status = ctk.CTkOptionMenu(
            barra, values=status_opcoes, width=120, height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._mudar_status_filtro,
        )
        self.opt_status.set("Status")
        self.opt_status.grid(row=1, column=3)

        # ── Cabeçalho fixo da tabela ──────────────────────────────
        cab_tab = ctk.CTkFrame(card, fg_color="#f0f0f0", corner_radius=0, height=28)
        cab_tab.grid(row=1, column=0, padx=8, sticky="ew")
        cab_tab.grid_propagate(False)
        for i, (rot, peso) in enumerate(COLUNAS):
            if rot == "Ações":
                cab_tab.grid_columnconfigure(i, weight=0, minsize=72)
            else:
                cab_tab.grid_columnconfigure(i, weight=peso)
            ctk.CTkLabel(
                cab_tab, text=rot,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#555555", anchor="w",
            ).grid(row=0, column=i, padx=(6, 0), pady=2, sticky="ew")

        # ── Área de rolagem ───────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(card, fg_color="white", corner_radius=0)
        self.scroll.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, peso) in enumerate(COLUNAS):
            if COLUNAS[i][0] == "Ações":
                self.scroll.grid_columnconfigure(i, weight=0, minsize=72)
            else:
                self.scroll.grid_columnconfigure(i, weight=peso)

        self._carregar_tabela()

    # ------------------------------------------------------------------
    # Painel direito: 4 cards de totais
    # ------------------------------------------------------------------
    def _criar_painel_direito(self):
        painel = ctk.CTkFrame(self, fg_color="transparent")
        painel.grid(row=1, column=1, padx=(0, 16), pady=(0, 16), sticky="nsew")
        painel.grid_columnconfigure(0, weight=1)

        definicoes = [
            ("total_mes",       "Total de Despesas (Mês)",      "#1a1a1a"),
            ("total_agendado",  "Total de Despesas (Agendado)", "#d97706"),
            ("total_em_aberto", "Total de Despesas (Em Aberto)","#e53935"),
            ("total_pago",      "Total de Despesas (Pago)",     "#2e7d32"),
        ]

        self._lbl_cards: dict[str, ctk.CTkLabel] = {}
        self._opt_mes_cards: dict[str, ctk.CTkOptionMenu] = {}

        for linha, (chave, titulo, cor) in enumerate(definicoes):
            card = ctk.CTkFrame(painel, fg_color="white", corner_radius=12)
            card.grid(row=linha, column=0, pady=(0, 10), sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card, text=titulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=cor, anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")

            lbl = ctk.CTkLabel(
                card, text="R$ 0,00",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color="#1a1a1a", anchor="w",
            )
            lbl.grid(row=1, column=0, padx=14, pady=(0, 2), sticky="w")
            self._lbl_cards[chave] = lbl

            # Seletor de mês individual por card
            opt = ctk.CTkOptionMenu(
                card, values=_MESES, width=120, height=28,
                font=ctk.CTkFont(size=11),
                command=lambda mes_nome, c=chave: self._atualizar_card(c, mes_nome),
            )
            opt.set(_MESES[self._mes_card[chave] - 1])
            opt.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")
            self._opt_mes_cards[chave] = opt

        # Card de despesas automáticas (fixas)
        self._criar_card_automaticas(painel, linha=len(definicoes))

        self._atualizar_todos_cards()

    # ------------------------------------------------------------------
    # Card Despesas Automáticas (fixas)
    # ------------------------------------------------------------------
    def _criar_card_automaticas(self, painel, linha: int):
        """Cria o card de despesas automáticas com mini-tabela."""
        card = ctk.CTkFrame(painel, fg_color="white", corner_radius=12)
        card.grid(row=linha, column=0, pady=(0, 10), sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Cabeçalho do card
        cab = ctk.CTkFrame(card, fg_color="transparent")
        cab.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
        cab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cab, text="Despesas Automáticas (fixas)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            cab, text="+ Criar Novo", width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._nova_auto,
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            card, text="Lista de acesso rápido de despesas.",
            font=ctk.CTkFont(size=11),
            text_color="#888888", anchor="w",
        ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")

        # Área de rolagem para a mini-tabela
        self._scroll_auto = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0, height=130,
        )
        self._scroll_auto.grid(row=2, column=0, padx=8, pady=(0, 10), sticky="ew")
        self._scroll_auto.grid_columnconfigure(0, weight=1)
        self._scroll_auto.grid_columnconfigure(1, weight=0, minsize=80)
        self._scroll_auto.grid_columnconfigure(2, weight=0, minsize=64)

        self._carregar_lista_auto()

    def _carregar_lista_auto(self):
        """Recarrega a mini-tabela de despesas automáticas."""
        for w in self._scroll_auto.winfo_children():
            w.destroy()

        autos = obter_lista_auto()

        # Cabeçalho da mini-tabela
        for col, (rot, ancora) in enumerate([("Descrição", "w"), ("Valor", "e"), ("Ações", "center")]):
            ctk.CTkLabel(
                self._scroll_auto, text=rot,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888", anchor=ancora,
            ).grid(row=0, column=col, padx=(6, 2), pady=(0, 4), sticky="ew")

        if not autos:
            ctk.CTkLabel(
                self._scroll_auto, text="Nenhuma despesa automática cadastrada.",
                font=ctk.CTkFont(size=11), text_color="#aaaaaa",
            ).grid(row=1, column=0, columnspan=3, pady=8)
            return

        for i, a in enumerate(autos, start=1):
            ctk.CTkLabel(
                self._scroll_auto, text=a["descricao"],
                font=ctk.CTkFont(size=11),
                text_color="#1a1a1a", anchor="w",
            ).grid(row=i, column=0, padx=(6, 2), pady=2, sticky="ew")

            ctk.CTkLabel(
                self._scroll_auto, text=formatar_moeda(a["valor"]),
                font=ctk.CTkFont(size=11),
                text_color="#1a1a1a", anchor="e",
            ).grid(row=i, column=1, padx=(0, 4), pady=2, sticky="ew")

            fa = ctk.CTkFrame(self._scroll_auto, fg_color="transparent")
            fa.grid(row=i, column=2, pady=2)

            ctk.CTkButton(
                fa, text="✏️", width=28, height=24,
                fg_color="#dbeafe", hover_color="#93c5fd",
                text_color="#000000", font=ctk.CTkFont(size=11),
                command=lambda aid=a["id"]: self._editar_auto(aid),
            ).grid(row=0, column=0, padx=(0, 2))

            ctk.CTkButton(
                fa, text="🗑️", width=28, height=24,
                fg_color="#fee2e2", hover_color="#fca5a5",
                text_color="#000000", font=ctk.CTkFont(size=11),
                command=lambda aid=a["id"]: self._excluir_auto(aid),
            ).grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Carregar / recarregar tabela
    # ------------------------------------------------------------------
    def _carregar_tabela(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        busca = self.entry_busca.get().strip()

        # Converte label de status para chave interna
        label_para_chave = {v: k for k, v in STATUS_LABELS.items()}
        status_chave = label_para_chave.get(self._status_filtro, "")

        despesas = obter_lista(
            busca=busca,
            mes=self._mes_tabela,
            ano=self._ano_tabela,
            status=status_chave,
        )

        if not despesas:
            ctk.CTkLabel(
                self.scroll, text="Nenhuma despesa encontrada.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=0, column=0, columnspan=len(COLUNAS), pady=20)
            return

        for linha, d in enumerate(despesas):
            cor_status = _STATUS_COR.get(d["status"], "#1a1a1a")
            dados_cols = [
                (d["descricao"],                    "#1a1a1a"),
                (d["data"],                         "#555555"),
                (d.get("responsavel") or "—",       "#1a1a1a"),
                (formatar_moeda(d["valor"]),         "#1a1a1a"),
                (d.get("forma_pagamento") or "—",   "#1a1a1a"),
                (d["status_label"],                 cor_status),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll, text=texto,
                    font=ctk.CTkFont(size=12,
                                     weight="bold" if col == 5 else "normal"),
                    text_color=cor, anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=3, sticky="ew")

            # Botões Editar / Excluir
            fa = ctk.CTkFrame(self.scroll, fg_color="transparent")
            fa.grid(row=linha, column=6, padx=(4, 6), pady=3)

            ctk.CTkButton(
                fa, text="✏️", width=30, height=26,
                fg_color="#dbeafe", hover_color="#93c5fd",
                text_color="#000000", font=ctk.CTkFont(size=13),
                command=lambda did=d["id"]: self._editar(did),
            ).grid(row=0, column=0, padx=(0, 2))

            ctk.CTkButton(
                fa, text="🗑️", width=30, height=26,
                fg_color="#fee2e2", hover_color="#fca5a5",
                text_color="#000000", font=ctk.CTkFont(size=13),
                command=lambda did=d["id"]: self._excluir(did),
            ).grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Ações CRUD
    # ------------------------------------------------------------------
    def _nova_despesa(self):
        DespesaForm(self, None, self._apos_salvar)

    def _editar(self, despesa_id: int):
        from controllers.despesa_controller import obter_por_id
        d = obter_por_id(despesa_id)
        if d:
            DespesaForm(self, d, self._apos_salvar)

    def _excluir(self, despesa_id: int):
        if not messagebox.askyesno("Excluir Despesa",
                                   "Deseja remover esta despesa permanentemente?"):
            return
        ok, msg = remover(despesa_id)
        if ok:
            self._apos_salvar()
        else:
            messagebox.showerror("Erro", msg)

    # Ações CRUD - Automáticas
    def _nova_auto(self):
        DespesaAutoForm(self, None, self._apos_salvar_auto)

    def _editar_auto(self, auto_id: int):
        d = obter_auto_por_id(auto_id)
        if d:
            DespesaAutoForm(self, d, self._apos_salvar_auto)

    def _excluir_auto(self, auto_id: int):
        if not messagebox.askyesno("Excluir Despesa Automática",
                                   "Deseja remover esta despesa automática permanentemente?\n"
                                   "(As despesas já geradas não serão removidas.)"):
            return
        ok, msg = remover_auto(auto_id)
        if ok:
            self._carregar_lista_auto()
        else:
            messagebox.showerror("Erro", msg)

    def _apos_salvar(self):
        """Recarrega tabela e cards após qualquer alteração."""
        self._carregar_tabela()
        self._atualizar_todos_cards()

    def _apos_salvar_auto(self):
        """Recarrega lista automática + tabela (novas despesas podem ter sido geradas)."""
        self._carregar_lista_auto()
        # Regenera despesas do mês atual após salvar nova auto
        gerar_despesas_mes_atual()
        self._carregar_tabela()
        self._atualizar_todos_cards()

    # ------------------------------------------------------------------
    # Filtros
    # ------------------------------------------------------------------
    def _mudar_mes_tabela(self, mes_nome: str):
        self._mes_tabela = _MESES.index(mes_nome) + 1
        self._carregar_tabela()

    def _mudar_status_filtro(self, valor: str):
        self._status_filtro = "" if valor == "Todos" else valor
        self._carregar_tabela()

    # ------------------------------------------------------------------
    # Cards de totais
    # ------------------------------------------------------------------
    def _atualizar_card(self, chave: str, mes_nome: str):
        """Atualiza um card individual ao mudar o mês selecionado."""
        mes = _MESES.index(mes_nome) + 1
        self._mes_card[chave] = mes
        resumo = obter_resumo(mes, self._ano_card)
        valor = resumo.get(chave, 0.0)
        self._lbl_cards[chave].configure(text=formatar_moeda(valor))

    def _atualizar_todos_cards(self):
        """Atualiza todos os 4 cards conforme o mês selecionado em cada um."""
        for chave, lbl in self._lbl_cards.items():
            mes = self._mes_card[chave]
            resumo = obter_resumo(mes, self._ano_card)
            valor = resumo.get(chave, 0.0)
            lbl.configure(text=formatar_moeda(valor))

    # ------------------------------------------------------------------
    # Impressão (stub)
    # ------------------------------------------------------------------
    def _imprimir(self):
        messagebox.showinfo(
            "Em breve",
            "A impressão do relatório de despesas será implementada em breve.",
        )
