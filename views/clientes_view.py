"""
clientes_view.py - Tela de listagem de Clientes.
Exibe tabela de clientes com busca, status de crédito e cards de resumo.
"""

import logging
import customtkinter as ctk
from tkinter import messagebox

from controllers.cliente_controller import obter_lista, obter_em_atraso, obter_resumo, remover
from utils import formatar_cpf, formatar_telefone, formatar_moeda

log = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Mapeamento de status → (texto, cor)
# ------------------------------------------------------------------
STATUS_INFO = {
    "sem_debitos": ("Sem débitos", "#1a1a1a"),
    "em_dia":      ("Em dia",      "#2e7d32"),
    "em_atraso":   ("Em atraso",   "#e53935"),
}

# ------------------------------------------------------------------
# Definição das colunas da tabela: (rótulo, largura_px)
# Limite de caracteres por coluna para truncamento com "..."
# ------------------------------------------------------------------
COLUNAS_TABELA = [
    ("ID",       70),
    ("Nome",    165),
    ("Telefone", 140),
    ("Cidade",   150),
    ("Status",   120),
    ("Ações",     90),
]

# Máximo de caracteres antes de truncar com "…" (por coluna)
_MAX_CHARS = [None, 20, 18, 18, None, None]


def _truncar(texto: str, max_chars: int | None) -> str:
    """Trunca texto longo com reticências para manter alinhamento da tabela."""
    if max_chars and len(texto) > max_chars:
        return texto[:max_chars - 1] + "…"
    return texto


class ClientesView(ctk.CTkFrame):
    def __init__(self, parent, controller, filtro_inicial: str = None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Rastreia o filtro ativo: None | "em_atraso"
        self._filtro_ativo = filtro_inicial

        # Layout: cabeçalho, busca, tabela (expande), cards
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._criar_cabecalho()
        self._criar_barra_busca()
        self._criar_tabela()
        self._criar_cards_resumo()

        self.carregar_clientes()
        log.info("ClientesView carregada.")

    # ------------------------------------------------------------------
    # Cabeçalho: título + botão Adicionar
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="👤  Clientes",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            frame,
            text="Adicionar Cliente",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=160,
            height=36,
            command=self._abrir_formulario,
        ).grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------
    # Barra de busca
    # ------------------------------------------------------------------
    def _criar_barra_busca(self):
        frame = ctk.CTkFrame(self, fg_color="#cccccc", corner_radius=12)
        frame.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            placeholder_text="Digite para buscar clientes em tempo real (nome, CPF, telefone, cidade)",
            font=ctk.CTkFont(size=13),
            height=40,
            border_width=0,
            fg_color="white",
            corner_radius=8,
        )
        self.entry_busca.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", self._ao_digitar_busca)

        ctk.CTkButton(
            frame,
            text="🔍  Buscar",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=110,
            height=40,
            command=self.carregar_clientes,
        ).grid(row=0, column=1, padx=(0, 12), pady=12)

        # Badge que aparece quando um filtro de card está ativo
        self.lbl_filtro_ativo = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e53935",
            fg_color="transparent",
        )
        self.lbl_filtro_ativo.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w")

    def _ao_digitar_busca(self, event=None):
        """Ao digitar, limpa o filtro de card e faz a busca normal."""
        if self._filtro_ativo is not None:
            self._filtro_ativo = None
            self._atualizar_visual_cards()
        self.carregar_clientes()

    # ------------------------------------------------------------------
    # Tabela de clientes
    # ------------------------------------------------------------------
    def _criar_tabela(self):
        """Container branco com cabeçalho e lista scrollável alinhados por largura fixa."""
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Título da tabela
        self.label_total = ctk.CTkLabel(
            container,
            text="Lista de Clientes",
            font=ctk.CTkFont(size=13),
            text_color="#444444",
        )
        self.label_total.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="w")

        # Área scrollável — cabeçalho renderizado dentro (row=0) para alinhamento perfeito
        self.scroll_frame = ctk.CTkScrollableFrame(
            container, fg_color="white", corner_radius=0,
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        for i, (_, largura) in enumerate(COLUNAS_TABELA):
            self.scroll_frame.grid_columnconfigure(i, minsize=largura, weight=0)
        self.scroll_frame.grid_columnconfigure(len(COLUNAS_TABELA), weight=1)

    # ------------------------------------------------------------------
    # Cards de resumo (parte inferior)
    # ------------------------------------------------------------------
    def _criar_cards_resumo(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_cards = {}
        self.frm_cards = {}

        # O card "em_atraso" é clicável como filtro
        CARDS_CLICAVEIS = {"em_atraso"}

        definicoes = [
            ("total",     "Total de Clientes",   "#1f6aa5"),
            ("em_dia",    "Clientes em Dia",      "#2e7d32"),
            ("em_atraso", "Clientes em Atraso",   "#e53935"),
        ]

        for col, (chave, titulo, cor) in enumerate(definicoes):
            card = ctk.CTkFrame(frame, fg_color="white", corner_radius=12)
            card.grid(row=0, column=col, padx=6, sticky="ew", ipady=10)
            card.grid_columnconfigure(0, weight=1)
            self.frm_cards[chave] = card

            lbl_titulo = ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=cor,
                justify="center",
            )
            lbl_titulo.grid(row=0, column=0, padx=10, pady=(14, 4))

            lbl_valor = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color="#1a1a1a",
            )
            lbl_valor.grid(row=1, column=0, padx=10, pady=(0, 14))
            self.lbl_cards[chave] = lbl_valor

            if chave in CARDS_CLICAVEIS:
                for widget in (card, lbl_titulo, lbl_valor):
                    widget.configure(cursor="hand2")
                    widget.bind("<Button-1>", lambda e, k=chave: self._aplicar_filtro(k))
                    widget.bind("<Enter>", lambda e, c=card: c.configure(fg_color="#f5f5f5"))
                    widget.bind("<Leave>", lambda e, c=card, k=chave: self._restaurar_cor_card(c, k))

    def _aplicar_filtro(self, filtro: str):
        """Ativa ou desativa um filtro de card (toggle)."""
        self._filtro_ativo = None if self._filtro_ativo == filtro else filtro
        self._atualizar_visual_cards()
        self.carregar_clientes()

    def _restaurar_cor_card(self, card: ctk.CTkFrame, chave: str):
        card.configure(fg_color="#fff0f0" if self._filtro_ativo == chave else "white")

    def _atualizar_visual_cards(self):
        """Atualiza highlight dos cards e badge de filtro ativo."""
        for chave, card in self.frm_cards.items():
            card.configure(fg_color="#fff0f0" if self._filtro_ativo == chave else "white")

        texto_badge = (
            "🔴  Filtro: Clientes em Atraso — clique no card novamente para remover"
            if self._filtro_ativo == "em_atraso" else ""
        )
        self.lbl_filtro_ativo.configure(text=texto_badge)

    # ------------------------------------------------------------------
    # Carregamento e renderização dos clientes
    # ------------------------------------------------------------------
    def carregar_clientes(self, *args):
        """Busca os clientes (com filtro de card ou busca textual) e renderiza as linhas."""
        if self._filtro_ativo == "em_atraso":
            clientes = obter_em_atraso()
        else:
            busca = self.entry_busca.get().strip()
            clientes = obter_lista(busca)

        total = len(clientes)
        self.label_total.configure(
            text=f"Lista de Clientes ({total} {'cliente' if total == 1 else 'clientes'})"
        )

        # Limpa linhas anteriores
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Cabeçalho dentro do scroll (row=0) — garante alinhamento perfeito com os dados
        for i, (rotulo, largura) in enumerate(COLUNAS_TABELA):
            ctk.CTkLabel(
                self.scroll_frame, text=rotulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#555555", width=largura, anchor="w",
                fg_color="#f0f0f0",
            ).grid(row=0, column=i, padx=(8, 0), pady=6, sticky="w")

        # Renderiza cada linha a partir de row=1
        for linha, c in enumerate(clientes, start=1):
            bg = "white" if linha % 2 == 1 else "#f9f9f9"
            self._criar_linha(linha, c, bg)

        # Atualiza visual e cards de resumo
        self._atualizar_visual_cards()
        self._atualizar_cards()

    def _criar_linha(self, linha: int, cliente: dict, bg: str):
        """Renderiza uma linha de cliente na tabela. Clicar abre o detalhe."""
        status = cliente["status_credito"]
        txt_status, cor_status = STATUS_INFO.get(status, ("—", "#1a1a1a"))

        telefone_fmt = formatar_telefone(cliente.get("telefone") or "")
        cpf_fmt      = formatar_cpf(cliente.get("cpf") or "")

        dados_cols = [
            (f"#{cliente['id']:02d}",                              "#555555",  False, COLUNAS_TABELA[0][1]),
            (_truncar(cliente["nome"], _MAX_CHARS[1]),             "#1f6aa5",  False, COLUNAS_TABELA[1][1]),
            (_truncar(telefone_fmt or "—", _MAX_CHARS[2]),        "#1a1a1a",  False, COLUNAS_TABELA[2][1]),
            (_truncar(cliente.get("cidade") or "—", _MAX_CHARS[3]),"#1a1a1a", False, COLUNAS_TABELA[3][1]),
            (txt_status,                                           cor_status, True,  COLUNAS_TABELA[4][1]),
        ]

        widgets_linha = []

        for col, (texto, cor, negrito, largura) in enumerate(dados_cols):
            lbl = ctk.CTkLabel(
                self.scroll_frame,
                text=texto,
                font=ctk.CTkFont(size=13, weight="bold" if negrito else "normal"),
                text_color=cor,
                anchor="w",
                width=largura,
                cursor="hand2",
            )
            lbl.grid(row=linha, column=col, padx=(8, 0), pady=6, sticky="w")
            widgets_linha.append(lbl)
            lbl.bind("<Button-1>", lambda e, cid=cliente["id"]: self._abrir_detalhe(cid))

        # Efeito hover no nome
        nome_lbl = widgets_linha[1]
        fonte_normal = ctk.CTkFont(size=13, underline=False)
        fonte_hover  = ctk.CTkFont(size=13, underline=True)
        nome_lbl.bind("<Enter>", lambda e: nome_lbl.configure(font=fonte_hover))
        nome_lbl.bind("<Leave>", lambda e: nome_lbl.configure(font=fonte_normal))

        # Botões de ação na coluna 5
        frame_acoes = ctk.CTkFrame(
            self.scroll_frame, fg_color="transparent", width=COLUNAS_TABELA[5][1]
        )
        frame_acoes.grid(row=linha, column=5, padx=(8, 0), pady=4, sticky="w")

        ctk.CTkButton(
            frame_acoes, text="✏️", width=32, height=28,
            fg_color="transparent", hover_color="#e0e0e0",
            text_color="#1f6aa5", font=ctk.CTkFont(size=15),
            command=lambda cid=cliente["id"]: self._abrir_formulario(cid),
        ).grid(row=0, column=0, padx=(0, 4))

        ctk.CTkButton(
            frame_acoes, text="🗑️", width=32, height=28,
            fg_color="transparent", hover_color="#fde8e8",
            text_color="#e53935", font=ctk.CTkFont(size=15),
            command=lambda cid=cliente["id"], nome=cliente["nome"]: self._confirmar_exclusao(cid, nome),
        ).grid(row=0, column=1)

    def _atualizar_cards(self):
        """Atualiza os valores dos 3 cards de resumo."""
        dados = obter_resumo()
        self.lbl_cards["total"].configure(text=str(dados["total"]))
        self.lbl_cards["em_dia"].configure(text=str(dados["em_dia"]))
        self.lbl_cards["em_atraso"].configure(text=str(dados["em_atraso"]))

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _abrir_detalhe(self, cliente_id: int):
        from views.clientes_view import ClientesView
        from views.cliente_detalhe import ClienteDetalhe

        def voltar():
            self.controller.mostrar_tela(ClientesView)

        self.controller.mostrar_tela(
            ClienteDetalhe,
            cliente_id=cliente_id,
            on_voltar=voltar,
        )

    def _abrir_formulario(self, cliente_id: int = None):
        from views.clientes_view import ClientesView
        from views.cliente_form import ClienteForm

        def voltar():
            self.controller.mostrar_tela(ClientesView)

        self.controller.mostrar_tela(
            ClienteForm,
            cliente_id=cliente_id,
            on_voltar=voltar,
        )

    def _confirmar_exclusao(self, cliente_id: int, nome: str):
        resposta = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja remover o cliente '{nome}'?\nEssa ação não pode ser desfeita.",
        )
        if resposta:
            ok, msg = remover(cliente_id)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_clientes()
            else:
                messagebox.showerror("Erro", msg)
