"""
carrinho_view.py - Tela do Carrinho de Compras (Etapa 4).
Painel esquerdo: Produtos Disponíveis + Itens no Carrinho.
Painel direito: Resumo do Pedido (implementado na Etapa 4 — Fase 2).
"""

import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from controllers.produto_controller import obter_lista
from controllers.venda_controller import finalizar_venda
from models.produto_model import buscar_por_codigo_barras
from models.cliente_model import listar_clientes
from utils import formatar_moeda

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Colunas das tabelas: (rótulo, peso_relativo)
# Os pesos definem a proporção de cada coluna (responsivo)
# ------------------------------------------------------------------
COLS_DISP = [("ID", 1), ("Produto", 5), ("Qtd.", 2), ("Preço", 2), ("Ações", 2)]
COLS_CARR = [("ID", 1), ("Produto", 5), ("Qtd.", 2), ("Preço", 2), ("Ações", 2)]

# Cores dos botões de filtro: [inativo_fg, ativo_fg, inativo_hover, ativo_hover]
_FILTRO_CORES = {
    "todos":         ["#3a9adf", "#1f6aa5", "#2a7abf", "#104a85"],
    "promocao":      ["#f5a623", "#d97706", "#d48810", "#b06004"],
    "pouco_estoque": ["#f07070", "#e53935", "#cc3535", "#b01818"],
}

# Taxas de cartão (referência interna do vendedor — não afeta o preço ao cliente)
_TAXA_DEBITO = 1.66
_TAXAS_CREDITO = {
    1: 2.0,  2: 3.0,  3: 4.0,  4: 5.0,  5: 6.0,  6: 7.0,
    7: 8.0,  8: 9.0,  9: 10.0, 10: 11.0, 11: 12.0, 12: 13.0,
}


class CarrinhoView(ctk.CTkFrame):
    """
    Tela do Carrinho de Compras.
    Layout dividido em 2 colunas:
    - Esquerda (weight=5): Produtos Disponíveis + Itens no Carrinho
    - Direita  (weight=4): Resumo do Pedido (Fase 2)
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Filtro ativo: "todos" | "promocao" | "pouco_estoque"
        self._filtro: str = "todos"

        # Carrinho em memória: lista de dicts (produto_id, nome, quantidade, preco_unitario, subtotal)
        self._carrinho: list[dict] = []

        # Estado do Resumo do Pedido (Fase 2)
        self._cliente_selecionado: dict | None = None
        self._modo_sem_cadastro: bool = False   # True = campo livre, sem busca no BD
        self._forma_pagamento: str = "dinheiro"
        self._tipo_cartao: str = "debito"
        self._parcelas: int = 1
        self._desconto_pct: float = 0.0
        self._venda_finalizada: bool = False
        self._ultima_venda_id: int | None = None
        self._dropdown_cliente: ctk.CTkToplevel | None = None

        # Controle de estado do painel Resumo do Pedido
        self._resumo_ativo: bool = False

        self.grid_columnconfigure(0, weight=1, uniform="painel")
        self.grid_columnconfigure(1, weight=1, uniform="painel")
        self.grid_rowconfigure(0, weight=0)  # título
        self.grid_rowconfigure(1, weight=1)  # conteúdo expande

        self._construir_ui()

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        # Título da tela
        frame_titulo = ctk.CTkFrame(self, fg_color="transparent")
        frame_titulo.grid(row=0, column=0, columnspan=2,
                          padx=20, pady=(18, 6), sticky="ew")
        ctk.CTkLabel(
            frame_titulo, text="🛒  Carrinho",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # Coluna esquerda
        esq = ctk.CTkFrame(self, fg_color="transparent")
        esq.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        esq.grid_columnconfigure(0, weight=1)
        esq.grid_rowconfigure(0, weight=3)
        esq.grid_rowconfigure(1, weight=2)

        self._criar_card_produtos(esq)
        self._criar_card_carrinho(esq)

        # Coluna direita — placeholder (Fase 2)
        self._criar_painel_direito()

        # Aplica estado inicial do resumo (inativo se carrinho vazio)
        self._toggle_resumo(len(self._carrinho) > 0)

    # ------------------------------------------------------------------
    # Painel direito — Resumo do Pedido (Fase 2 completa)
    # ------------------------------------------------------------------
    def _criar_painel_direito(self):
        """Cria o painel direito completo: Resumo do Pedido."""
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        card.grid(row=1, column=1, padx=(8, 16), pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)  # scroll ocupa todo o espaço disponível
        self._painel_dir = card

        # Área de conteúdo rolável — padding lateral preserva cantos arredondados do card
        sc = ctk.CTkScrollableFrame(card, fg_color="white", corner_radius=12)
        sc.grid(row=0, column=0, padx=2, pady=(2, 0), sticky="nsew")
        sc.grid_columnconfigure(0, weight=1)

        # ── Título ───────────────────────────────────────────────
        ctk.CTkLabel(
            sc, text="Resumo do Pedido",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        # ── Totais (subtotal / desconto / total) ────────────────────
        tot = ctk.CTkFrame(sc, fg_color="#f7f7f7", corner_radius=8)
        tot.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        tot.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tot, text="Subtotal:",
            font=ctk.CTkFont(size=12), text_color="#666666",
        ).grid(row=0, column=0, padx=(10, 4), pady=(8, 2), sticky="w")
        self.lbl_subtotal = ctk.CTkLabel(
            tot, text="R$ 0,00",
            font=ctk.CTkFont(size=12), text_color="#1a1a1a",
        )
        self.lbl_subtotal.grid(row=0, column=1, padx=(0, 10), pady=(8, 2), sticky="e")

        # Linha de desconto
        desc_row = ctk.CTkFrame(tot, fg_color="transparent")
        desc_row.grid(row=1, column=0, columnspan=2, padx=6, pady=(0, 4), sticky="ew")
        desc_row.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            desc_row, text="Desconto %:",
            font=ctk.CTkFont(size=12), text_color="#666666",
        ).grid(row=0, column=0, sticky="w", padx=(4, 6))
        self.entry_desconto = ctk.CTkEntry(
            desc_row, width=58, height=26, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=12),
            placeholder_text="0",
        )
        self.entry_desconto.grid(row=0, column=1)
        self._btn_aplicar_desconto = ctk.CTkButton(
            desc_row, text="Aplicar", width=60, height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._aplicar_desconto,
        )
        self._btn_aplicar_desconto.grid(row=0, column=2, padx=(6, 0), sticky="w")
        self.lbl_desconto_val = ctk.CTkLabel(
            desc_row, text="",
            font=ctk.CTkFont(size=11), text_color="#e53935",
        )
        self.lbl_desconto_val.grid(row=0, column=3, padx=(8, 4), sticky="e")

        # Destaque do total
        tot_inner = ctk.CTkFrame(tot, fg_color="#dbeafe", corner_radius=6)
        tot_inner.grid(row=2, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        tot_inner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            tot_inner, text="Total:",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#1e3a5f",
        ).grid(row=0, column=0, padx=(10, 4), pady=7, sticky="w")
        self.lbl_total = ctk.CTkLabel(
            tot_inner, text="R$ 0,00",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5",
        )
        self.lbl_total.grid(row=0, column=1, padx=(0, 10), pady=7, sticky="e")

        # ── Separador ─────────────────────────────────────────
        ctk.CTkFrame(sc, fg_color="#e0e0e0", height=1, corner_radius=0).grid(
            row=2, column=0, padx=12, pady=(0, 6), sticky="ew"
        )

        # ── Cliente ───────────────────────────────────────────
        ctk.CTkLabel(
            sc, text="Cliente",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#333333", anchor="w",
        ).grid(row=3, column=0, padx=14, pady=(0, 4), sticky="w")

        cli_frame = ctk.CTkFrame(sc, fg_color="transparent")
        cli_frame.grid(row=4, column=0, padx=12, pady=(0, 4), sticky="ew")
        cli_frame.grid_columnconfigure(0, weight=1)

        self.entry_cliente_busca = ctk.CTkEntry(
            cli_frame, height=32, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=12),
            placeholder_text="Digite 3 letras do nome...",
        )
        self.entry_cliente_busca.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        self.entry_cliente_busca.bind("<KeyRelease>", self._buscar_cliente)
        self.entry_cliente_busca.bind("<Escape>", lambda e: self._fechar_dropdown_cliente())

        self._btn_sem_cadastro = ctk.CTkButton(
            cli_frame, text="Sem Cadastro", width=100, height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#888888", hover_color="#666666",
            command=self._toggle_sem_cadastro,
        )
        self._btn_sem_cadastro.grid(row=0, column=1)

        # Faixa que exibe o cliente selecionado (inicialmente oculta)
        self.frame_cli_sel = ctk.CTkFrame(sc, fg_color="#f0f7ff", corner_radius=6)
        self.frame_cli_sel.grid_columnconfigure(0, weight=1)
        self.lbl_cli_nome = ctk.CTkLabel(
            self.frame_cli_sel, text="",
            font=ctk.CTkFont(size=12), text_color="#1f6aa5", anchor="w",
        )
        self.lbl_cli_nome.grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")
        ctk.CTkButton(
            self.frame_cli_sel, text="✕", width=24, height=24,
            fg_color="#e53935", hover_color="#c62828",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._remover_cliente,
        ).grid(row=0, column=1, padx=(0, 6), pady=5)
        # salvar grid info e ocultar
        self.frame_cli_sel.grid(row=5, column=0, padx=12, pady=(0, 4), sticky="ew")
        self.frame_cli_sel.grid_remove()

        # ── Separador ─────────────────────────────────────────
        ctk.CTkFrame(sc, fg_color="#e0e0e0", height=1, corner_radius=0).grid(
            row=6, column=0, padx=12, pady=(0, 6), sticky="ew"
        )

        # ── Forma de Pagamento ────────────────────────────
        ctk.CTkLabel(
            sc, text="Forma de Pagamento",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#333333", anchor="w",
        ).grid(row=7, column=0, padx=14, pady=(0, 4), sticky="w")

        fp_frame = ctk.CTkFrame(sc, fg_color="transparent")
        fp_frame.grid(row=8, column=0, padx=12, pady=(0, 6), sticky="ew")
        _formas = [
            ("Dinheiro", "dinheiro"),
            ("PIX",      "pix"),
            ("Cartão",   "cartao"),
            ("Prazo",    "a_prazo"),
        ]
        self._btns_forma: dict[str, ctk.CTkButton] = {}
        for col, (label, chave) in enumerate(_formas):
            btn = ctk.CTkButton(
                fp_frame, text=label, height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda c=chave: self._selecionar_forma(c),
            )
            btn.grid(row=0, column=col, padx=(0, 4) if col < 3 else 0, sticky="ew")
            fp_frame.grid_columnconfigure(col, weight=1)
            self._btns_forma[chave] = btn
        self._atualizar_cores_forma()

        # ── Painel dinâmico de pagamento ─────────────────────
        self.frame_pagamento = ctk.CTkFrame(sc, fg_color="transparent")
        self.frame_pagamento.grid(row=9, column=0, padx=12, pady=(0, 12), sticky="ew")
        self.frame_pagamento.grid_columnconfigure(0, weight=1)
        self._mostrar_painel_pagamento()

        # ── Botões de ação fixos fora do scroll ───────────────
        sep_btn = ctk.CTkFrame(card, fg_color="#e0e0e0", height=1, corner_radius=0)
        sep_btn.grid(row=1, column=0, padx=0, pady=0, sticky="ew")

        self.btn_finalizar = ctk.CTkButton(
            card, text="✅  Finalizar Compra", height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._finalizar_compra,
        )
        self.btn_finalizar.grid(row=2, column=0, padx=12, pady=(8, 4), sticky="ew")

        self.btn_limpar_imprimir = ctk.CTkButton(
            card, text="🗑️  Limpar Carrinho", height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#888888", hover_color="#666666",
            command=self._acao_limpar_ou_imprimir,
        )
        self.btn_limpar_imprimir.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

    # ------------------------------------------------------------------
    # Card: Produtos Disponíveis
    # ------------------------------------------------------------------
    def _criar_card_produtos(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, pady=(0, 8), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)  # scroll expande

        # Título
        ctk.CTkLabel(
            card, text="Produtos Disponíveis",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        # Barra de busca
        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        barra.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            barra,
            placeholder_text="Digite para buscar produtos...",
            height=36, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=13),
        )
        self.entry_busca.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._carregar_produtos())
        self.entry_busca.bind("<Return>", lambda e: self._escanear_produto())

        ctk.CTkButton(
            barra, text="🔍 Buscar", width=92, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._carregar_produtos,
        ).grid(row=0, column=1)

        # Botões de filtro
        fb = ctk.CTkFrame(card, fg_color="transparent")
        fb.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="w")

        self.btn_todos = ctk.CTkButton(
            fb, text="Todos", width=82, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["todos"][1],
            hover_color=_FILTRO_CORES["todos"][3],
            command=lambda: self._aplicar_filtro("todos"),
        )
        self.btn_todos.grid(row=0, column=0, padx=(0, 6))

        self.btn_promocao = ctk.CTkButton(
            fb, text="Promoção", width=90, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["promocao"][0],
            hover_color=_FILTRO_CORES["promocao"][2],
            command=lambda: self._aplicar_filtro("promocao"),
        )
        self.btn_promocao.grid(row=0, column=1, padx=(0, 6))

        self.btn_pouco_est = ctk.CTkButton(
            fb, text="Pouco Estoque", width=118, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["pouco_estoque"][0],
            hover_color=_FILTRO_CORES["pouco_estoque"][2],
            command=lambda: self._aplicar_filtro("pouco_estoque"),
        )
        self.btn_pouco_est.grid(row=0, column=2)

        # Área de rolagem dos produtos — cabeçalho renderizado dentro (row=0)
        self.scroll_produtos = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_produtos.grid(row=3, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, peso) in enumerate(COLS_DISP):
            self.scroll_produtos.grid_columnconfigure(i, weight=peso)
        # Coluna de Ações: largura fixa (ajuste minsize para testar)
        self.scroll_produtos.grid_columnconfigure(len(COLS_DISP) - 1, weight=0, minsize=100)

        self._carregar_produtos()

    # ------------------------------------------------------------------
    # Card: Itens no Carrinho
    # ------------------------------------------------------------------
    def _criar_card_carrinho(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        self.lbl_titulo_carr = ctk.CTkLabel(
            card, text="Itens no Carrinho (0)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        )
        self.lbl_titulo_carr.grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        # Área de rolagem do carrinho — cabeçalho renderizado dentro (row=0)
        self.scroll_carrinho = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_carrinho.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, peso) in enumerate(COLS_CARR):
            self.scroll_carrinho.grid_columnconfigure(i, weight=peso)
        # Coluna de Ações: largura fixa (ajuste minsize para testar)
        self.scroll_carrinho.grid_columnconfigure(len(COLS_CARR) - 1, weight=0, minsize=100)

        self._recarregar_carrinho()

    # ------------------------------------------------------------------
    # Utilitário: cabeçalho de tabela dentro do scroll (row=0)
    # ------------------------------------------------------------------
    def _inserir_cabecalho(self, scroll, colunas: list):
        """Renderiza o cabeçalho como primeira linha do CTkScrollableFrame."""
        for i, (rot, _) in enumerate(colunas):
            ctk.CTkLabel(
                scroll, text=rot,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#555555", anchor="w",
                fg_color="#f0f0f0",
            ).grid(row=0, column=i, padx=(6, 0), pady=(2, 4), sticky="ew")

    # ------------------------------------------------------------------
    # Filtros e carregamento de produtos
    # ------------------------------------------------------------------
    def _aplicar_filtro(self, filtro: str):
        """Altera o filtro ativo, limpa a busca e recarrega a lista."""
        self._filtro = filtro
        self.entry_busca.delete(0, "end")
        self._carregar_produtos()

    def _escanear_produto(self):
        """Chamado ao pressionar Enter (ou pelo leitor de código de barras).
        Se o código digitado corresponde exatamente a um produto cadastrado,
        adiciona direto ao carrinho e limpa o campo.
        """
        codigo = self.entry_busca.get().strip()
        if not codigo:
            return

        # Tenta correspondência exata por código de barras
        produto = buscar_por_codigo_barras(codigo)
        if produto:
            self._adicionar_ao_carrinho(produto)
            self.entry_busca.delete(0, "end")
            self._carregar_produtos()  # restaura lista completa
            return

        # Sem correspondência exata — mantém a busca normal exibida
        self._carregar_produtos()

    def _carregar_produtos(self):
        """Atualiza a tabela de produtos conforme busca e filtro ativo."""
        busca  = self.entry_busca.get().strip()
        todos  = obter_lista(busca)

        # Contagens para os botões de filtro
        n_promo = sum(1 for p in todos if p.get("status_estoque") == "estoque_alto")
        n_pouco = sum(
            1 for p in todos
            if p.get("status_estoque") in ("estoque_baixo", "sem_estoque")
        )

        self.btn_todos.configure(text=f"Todos ({len(todos)})")
        self.btn_promocao.configure(text=f"Promoção ({n_promo})")
        self.btn_pouco_est.configure(text=f"Pouco Estoque ({n_pouco})")

        # Destaque visual do filtro ativo
        self._atualizar_cores_filtro()

        # Aplica o filtro selecionado
        if self._filtro == "promocao":
            produtos = [p for p in todos if p.get("status_estoque") == "estoque_alto"]
        elif self._filtro == "pouco_estoque":
            produtos = [
                p for p in todos
                if p.get("status_estoque") in ("estoque_baixo", "sem_estoque")
            ]
        else:
            produtos = todos

        # Limpa e preenche o scroll de produtos
        for w in self.scroll_produtos.winfo_children():
            w.destroy()

        # Cabeçalho dentro do scroll — alinhamento perfeito com as colunas
        self._inserir_cabecalho(self.scroll_produtos, COLS_DISP)

        if not produtos:
            ctk.CTkLabel(
                self.scroll_produtos,
                text="Nenhum produto encontrado.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=1, column=0, columnspan=len(COLS_DISP), pady=14)
            return

        for linha, p in enumerate(produtos, start=1):
            dados_cols = [
                (f"#{p['id']:02d}",          "#555555"),
                (p["nome"],                    "#1f6aa5"),
                (str(p["quantidade"]),         "#1a1a1a"),
                (formatar_moeda(p["preco"]),   "#1a1a1a"),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll_produtos, text=texto,
                    font=ctk.CTkFont(size=12), text_color=cor,
                    anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="ew")

            ctk.CTkButton(
                self.scroll_produtos, text="+ Adic.", width=72, height=24,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda prod=p: self._adicionar_ao_carrinho(prod),
            ).grid(row=linha, column=len(COLS_DISP) - 1, padx=(4, 4), pady=2)

    def _atualizar_cores_filtro(self):
        """Aplica cor de destaque (escura) ao botão do filtro atualmente ativo."""
        mapa = {
            "todos":         self.btn_todos,
            "promocao":      self.btn_promocao,
            "pouco_estoque": self.btn_pouco_est,
        }
        for chave, btn in mapa.items():
            ativo      = (chave == self._filtro)
            idx_fg    = 1 if ativo else 0
            idx_hover = 3 if ativo else 2
            btn.configure(
                fg_color=_FILTRO_CORES[chave][idx_fg],
                hover_color=_FILTRO_CORES[chave][idx_hover],
            )

    # ------------------------------------------------------------------
    # Carrinho: adicionar, editar, remover
    # ------------------------------------------------------------------
    def _adicionar_ao_carrinho(self, produto: dict):
        """Adiciona produto ao carrinho; incrementa quantidade se já estiver."""
        for item in self._carrinho:
            if item["produto_id"] == produto["id"]:
                item["quantidade"] += 1
                item["subtotal"] = round(item["quantidade"] * item["preco_unitario"], 2)
                self._recarregar_carrinho()
                return

        self._carrinho.append({
            "produto_id":     produto["id"],
            "nome":           produto["nome"],
            "quantidade":     1,
            "preco_unitario": produto["preco"],
            "subtotal":       produto["preco"],
        })
        self._recarregar_carrinho()

    def _recarregar_carrinho(self):
        """Atualiza a tabela do carrinho e aciona a atualização do resumo."""
        for w in self.scroll_carrinho.winfo_children():
            w.destroy()

        n = len(self._carrinho)
        self.lbl_titulo_carr.configure(text=f"Itens no Carrinho ({n})")

        # Cabeçalho dentro do scroll — alinhamento perfeito com as colunas
        self._inserir_cabecalho(self.scroll_carrinho, COLS_CARR)

        if not self._carrinho:
            ctk.CTkLabel(
                self.scroll_carrinho, text="Nenhum item no carrinho.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=1, column=0, columnspan=len(COLS_CARR), pady=14)
            self._atualizar_resumo()
            self._toggle_resumo(False)
            return

        for idx, item in enumerate(self._carrinho):
            linha = idx + 1
            dados_cols = [
                (f"#{item['produto_id']:02d}", "#555555"),
                (item["nome"],                  "#1f6aa5"),
                (str(item["quantidade"]),        "#1a1a1a"),
                (formatar_moeda(item["subtotal"]), "#1a1a1a"),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll_carrinho, text=texto,
                    font=ctk.CTkFont(size=12), text_color=cor,
                    anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="ew")

            # Botões por linha: Editar e Excluir (tamanho fixo)
            fa = ctk.CTkFrame(self.scroll_carrinho, fg_color="transparent")
            fa.grid(row=linha, column=4, padx=(2, 4), pady=2, sticky="ew")

            ctk.CTkButton(
                fa, text="✏️", width=34, height=26,
                fg_color="#dbeafe", hover_color="#93c5fd",
                font=ctk.CTkFont(size=13), text_color="#000000",
                command=lambda i=idx: self._editar_item(i),
            ).grid(row=0, column=0, padx=(0, 2))
            ctk.CTkButton(
                fa, text="🗑️", width=34, height=26,
                fg_color="#fee2e2", hover_color="#fca5a5",
                font=ctk.CTkFont(size=13), text_color="#000000",
                command=lambda i=idx: self._remover_item(i),
            ).grid(row=0, column=1)

        self._atualizar_resumo()
        self._toggle_resumo(True)

    def _editar_item(self, indice: int):
        """Abre popup modal para editar quantidade e preço de um item do carrinho."""
        _EditarItemForm(self, self._carrinho[indice], self._recarregar_carrinho)

    def _remover_item(self, indice: int):
        """Remove um item do carrinho e atualiza a tabela."""
        self._carrinho.pop(indice)
        self._recarregar_carrinho()

    # ------------------------------------------------------------------
    # Resumo do Pedido — atualização de totais
    # ------------------------------------------------------------------
    def _atualizar_resumo(self):
        """Recalcula subtotal, desconto e total e atualiza os rótulos do painel direito."""
        if not hasattr(self, "lbl_subtotal"):
            return

        subtotal     = sum(item["subtotal"] for item in self._carrinho)
        desconto_val = round(subtotal * self._desconto_pct / 100, 2)
        total        = round(subtotal - desconto_val, 2)

        self.lbl_subtotal.configure(text=formatar_moeda(subtotal))
        self.lbl_total.configure(text=formatar_moeda(total))

        if desconto_val > 0:
            self.lbl_desconto_val.configure(text=f"- {formatar_moeda(desconto_val)}")
        else:
            self.lbl_desconto_val.configure(text="")

        # Atualiza valor da parcela no painel de cartão crédito
        if (
            self._forma_pagamento == "cartao"
            and self._tipo_cartao == "credito"
            and hasattr(self, "lbl_valor_parcela")
            and self._parcelas > 0
        ):
            vp = total / self._parcelas
            self.lbl_valor_parcela.configure(text=f"Valor da Parcela: {formatar_moeda(vp)}")

    def _limpar_carrinho(self):
        """Esvazia todo o carrinho."""
        self._carrinho.clear()
        self._recarregar_carrinho()

    # ------------------------------------------------------------------
    # Fase 2: desconto
    # ------------------------------------------------------------------
    def _aplicar_desconto(self):
        """Lê o percentual do entry e atualiza o total."""
        try:
            pct = float(self.entry_desconto.get().strip().replace(",", "."))
            if pct < 0 or pct > 100:
                raise ValueError
            self._desconto_pct = pct
        except ValueError:
            messagebox.showerror("Erro", "Digite um desconto v\u00e1lido entre 0 e 100.")
            return
        self._atualizar_resumo()

    # ------------------------------------------------------------------
    # Fase 2: busca e sele\u00e7\u00e3o de cliente
    # ------------------------------------------------------------------
    def _buscar_cliente(self, event=None):
        """Abre dropdown com sugestões de cliente a partir de 3 caracteres."""
        # Modo sem cadastro: campo é texto livre, sem consulta ao BD
        if self._modo_sem_cadastro:
            return

        texto = self.entry_cliente_busca.get().strip()

        # Fecha dropdown anterior
        self._fechar_dropdown_cliente()

        if len(texto) < 3:
            return

        clientes = listar_clientes(texto)
        if not clientes:
            return

        entry = self.entry_cliente_busca

        # Coordenadas absolutas de tela — posiciona exatamente sob o campo de busca
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height() + 2
        w = entry.winfo_width()
        h = min(len(clientes[:8]) * 36 + 6, 180)

        # tk.Toplevel puro: sem decoração, sem os problemas de z-order do CTkToplevel
        dd = tk.Toplevel(self)
        dd.wm_overrideredirect(True)
        dd.geometry(f"{w}x{h}+{x}+{y}")
        dd.lift()
        dd.attributes("-topmost", True)

        scroll = ctk.CTkScrollableFrame(dd, fg_color="white")
        scroll.pack(fill="both", expand=True)

        for c in clientes[:8]:
            ctk.CTkButton(
                scroll,
                text=c["nome"],
                anchor="w",
                fg_color="white",
                hover_color="#dbeafe",
                text_color="#1a1a1a",
                font=ctk.CTkFont(size=12),
                height=30,
                command=lambda cli=c: self._selecionar_cliente(cli),
            ).pack(fill="x", padx=2, pady=1)

        self._dropdown_cliente = dd

    def _fechar_dropdown_cliente(self):
        """Fecha o dropdown de sugest\u00f5es de cliente."""
        if self._dropdown_cliente and self._dropdown_cliente.winfo_exists():
            self._dropdown_cliente.destroy()

    def _selecionar_cliente(self, cliente: dict):
        """Fixa o cliente e exibe a faixa de confirma\u00e7\u00e3o."""
        # Sair do modo sem cadastro caso estivesse ativo
        self._modo_sem_cadastro = False
        self._restaurar_entry_cliente()
        self._cliente_selecionado = cliente
        self.entry_cliente_busca.delete(0, "end")
        self._fechar_dropdown_cliente()
        self.lbl_cli_nome.configure(text=f"\ud83d\udc64  {cliente['nome']}")
        self.frame_cli_sel.grid()
        self._atualizar_cor_sem_cadastro()
        # Atualiza aviso de prazo sem cliente, se n\u00e3o houver mais
        if self._forma_pagamento == "a_prazo":
            self._mostrar_painel_pagamento()

    def _remover_cliente(self):
        """Remove o cliente selecionado (chamado pelo botão ✕ na faixa)."""
        self._cliente_selecionado = None
        self._modo_sem_cadastro = False
        self._restaurar_entry_cliente()
        self.entry_cliente_busca.delete(0, "end")
        self.frame_cli_sel.grid_remove()
        self._atualizar_cor_sem_cadastro()
        if self._forma_pagamento == "a_prazo":
            self._mostrar_painel_pagamento()

    def _toggle_sem_cadastro(self):
        """Alterna o modo Sem Cadastro.

        Cinza (inativo): campo busca clientes cadastrados normalmente.
        Verde (ativo):   campo vira texto livre para digitar nome avulso.
        """
        if self._modo_sem_cadastro:
            # Desativar: voltar ao modo normal
            self._modo_sem_cadastro = False
            self._cliente_selecionado = None
            self._restaurar_entry_cliente()
            self.entry_cliente_busca.delete(0, "end")
            self.frame_cli_sel.grid_remove()
        else:
            # Ativar: limpar cliente e liberar campo livre
            self._modo_sem_cadastro = True
            self._cliente_selecionado = None
            self._fechar_dropdown_cliente()
            self.frame_cli_sel.grid_remove()
            self.entry_cliente_busca.delete(0, "end")
            self.entry_cliente_busca.configure(
                placeholder_text="Nome do cliente (opcional)...",
                border_color="#2e7d32",
            )
        self._atualizar_cor_sem_cadastro()
        if self._forma_pagamento == "a_prazo":
            self._mostrar_painel_pagamento()

    def _restaurar_entry_cliente(self):
        """Restaura o campo de busca de cliente para o modo padrão."""
        if hasattr(self, "entry_cliente_busca"):
            self.entry_cliente_busca.configure(
                placeholder_text="Digite 3 letras do nome...",
                border_color="#cccccc",
            )

    def _atualizar_cor_sem_cadastro(self):
        """Verde quando o modo Sem Cadastro está ativo, cinza caso contrário."""
        if not hasattr(self, "_btn_sem_cadastro"):
            return
        self._btn_sem_cadastro.configure(
            fg_color="#2e7d32" if self._modo_sem_cadastro else "#888888",
            hover_color="#1b5e20" if self._modo_sem_cadastro else "#666666",
        )

    # ------------------------------------------------------------------
    # Fase 2: forma de pagamento
    # ------------------------------------------------------------------
    def _selecionar_forma(self, forma: str):
        """Altera a forma de pagamento ativa e reconstr\u00f3i o painel din\u00e2mico."""
        self._forma_pagamento = forma
        self._atualizar_cores_forma()
        self._mostrar_painel_pagamento()

    def _atualizar_cores_forma(self):
        """Destaca visualmente o bot\u00e3o da forma de pagamento ativa."""
        if not hasattr(self, "_btns_forma"):
            return
        for chave, btn in self._btns_forma.items():
            ativo = (chave == self._forma_pagamento)
            btn.configure(
                fg_color="#2e7d32" if ativo else "#3a9adf",
                hover_color="#1b5e20" if ativo else "#2a7abf",
            )

    def _mostrar_painel_pagamento(self):
        """Reconstr\u00f3i o painel din\u00e2mico conforme a forma selecionada."""
        for w in self.frame_pagamento.winfo_children():
            w.destroy()
        if self._forma_pagamento == "cartao":
            self._construir_painel_cartao()
        else:
            self._construir_painel_simples()
        # Re-aplica disabled se o resumo ainda estiver inativo
        if not self._resumo_ativo:
            for w in self.frame_pagamento.winfo_children():
                self._toggle_widget_recursivo(w, "disabled")

    # ------------------------------------------------------------------
    # Controle visual do Resumo do Pedido (ativo/inativo)
    # ------------------------------------------------------------------
    def _toggle_resumo(self, ativo: bool):
        """Ativa ou desativa visualmente o painel Resumo do Pedido.
        Quando inativo (carrinho vazio), o card fica acinzentado e todos
        os controles interativos ficam desabilitados.
        """
        self._resumo_ativo = ativo

        # Painel direito ainda não foi construído (chamada durante __init__)
        if not hasattr(self, "_painel_dir"):
            return

        state = "normal" if ativo else "disabled"

        # Cor de fundo do card
        self._painel_dir.configure(fg_color="white" if ativo else "#efefef")

        # Widgets estaticos interativos
        widgets_estaticos = [
            self.entry_desconto,
            self._btn_aplicar_desconto,
            self.entry_cliente_busca,
            self._btn_sem_cadastro,
            self.btn_finalizar,
            self.btn_limpar_imprimir,
        ]
        for w in widgets_estaticos:
            try:
                w.configure(state=state)
            except Exception:
                pass

        # Botoes de forma de pagamento
        for btn in self._btns_forma.values():
            try:
                btn.configure(state=state)
            except Exception:
                pass

        # Widgets do painel dinamico de pagamento
        for w in self.frame_pagamento.winfo_children():
            self._toggle_widget_recursivo(w, state)

    def _toggle_widget_recursivo(self, widget, state: str):
        """Aplica state recursivamente em widgets descendentes."""
        try:
            widget.configure(state=state)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._toggle_widget_recursivo(child, state)

    def _construir_painel_simples(self):
        """Painel de Dinheiro / PIX / Prazo."""
        inner = ctk.CTkFrame(self.frame_pagamento, fg_color="#f7f7f7", corner_radius=8)
        inner.grid(row=0, column=0, sticky="ew")
        inner.grid_columnconfigure(1, weight=1)

        nomes = {"dinheiro": "Dinheiro", "pix": "PIX", "a_prazo": "Prazo"}
        titulo = nomes.get(self._forma_pagamento, "Valor")

        ctk.CTkLabel(
            inner, text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#333333",
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 4), sticky="w")

        # Prazo: sem campo de valor — vai para o crediário do cliente
        if self._forma_pagamento == "a_prazo":
            msg = (
                "⚠️  Selecione um cliente para venda a prazo."
                if not self._cliente_selecionado
                else f"✅  O valor será lançado no crediário de {self._cliente_selecionado['nome']}."
            )
            cor = "#e53935" if not self._cliente_selecionado else "#2e7d32"
            ctk.CTkLabel(
                inner, text=msg,
                font=ctk.CTkFont(size=11), text_color=cor,
                wraplength=280, justify="left",
            ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
            return

        # Dinheiro / PIX: campo de valor + troco
        ctk.CTkLabel(
            inner, text="R$", font=ctk.CTkFont(size=13), text_color="#444444",
        ).grid(row=1, column=0, padx=(10, 4), pady=(0, 4), sticky="w")

        self.entry_valor_pago = ctk.CTkEntry(
            inner, height=30, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            placeholder_text="Digite o valor recebido...",
        )
        self.entry_valor_pago.grid(row=1, column=1, padx=(0, 10), pady=(0, 4), sticky="ew")
        self.entry_valor_pago.bind("<KeyRelease>", self._calcular_troco)

        # Linha de troco (inicialmente vazia)
        self.lbl_troco = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#2e7d32",
            anchor="e",
        )
        self.lbl_troco.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="ew")

    def _calcular_troco(self, event=None):
        """Atualiza o rótulo de troco conforme o valor digitado."""
        if not hasattr(self, "lbl_troco") or not self.lbl_troco.winfo_exists():
            return
        try:
            valor_pago = float(
                self.entry_valor_pago.get().strip().replace(",", ".")
            )
        except ValueError:
            self.lbl_troco.configure(text="")
            return

        subtotal     = sum(item["subtotal"] for item in self._carrinho)
        desconto_val = round(subtotal * self._desconto_pct / 100, 2)
        total        = round(subtotal - desconto_val, 2)
        troco        = round(valor_pago - total, 2)

        if troco >= 0:
            self.lbl_troco.configure(
                text=f"Troco: {formatar_moeda(troco)}",
                text_color="#2e7d32",
            )
        else:
            self.lbl_troco.configure(
                text=f"Faltam: {formatar_moeda(abs(troco))}",
                text_color="#e53935",
            )

    def _construir_painel_cartao(self):
        """Painel de Cart\u00e3o: D\u00e9bito / Cr\u00e9dito + parcelas (apenas cr\u00e9dito)."""
        inner = ctk.CTkFrame(self.frame_pagamento, fg_color="#f7f7f7", corner_radius=8)
        inner.grid(row=0, column=0, sticky="ew")
        inner.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            inner, text="Cart\u00e3o",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#333333",
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 6), sticky="w")

        # Bot\u00f5es D\u00e9bito / Cr\u00e9dito
        tipos = ctk.CTkFrame(inner, fg_color="transparent")
        tipos.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="ew")
        tipos.grid_columnconfigure((0, 1), weight=1)

        self.btn_debito = ctk.CTkButton(
            tipos, text="D\u00e9bito", height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._selecionar_tipo_cartao("debito"),
        )
        self.btn_debito.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_credito = ctk.CTkButton(
            tipos, text="Cr\u00e9dito", height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._selecionar_tipo_cartao("credito"),
        )
        self.btn_credito.grid(row=0, column=1, padx=(4, 0), sticky="ew")
        self._atualizar_cores_tipo_cartao()

        # Informação de taxa + valor líquido para o estabelecimento
        subtotal_taxa  = sum(item["subtotal"] for item in self._carrinho)
        desconto_taxa  = round(subtotal_taxa * self._desconto_pct / 100, 2)
        total_taxa     = round(subtotal_taxa - desconto_taxa, 2)
        if self._tipo_cartao == "debito":
            pct_taxa   = _TAXA_DEBITO
        else:
            pct_taxa   = _TAXAS_CREDITO.get(self._parcelas, 0.0)
        valor_liquido  = round(total_taxa * (1 - pct_taxa / 100), 2)
        taxa_str = (
            f"Taxa interna: {pct_taxa:.2f}%"
            f"    —    Valor para o estabelecimento: {formatar_moeda(valor_liquido)}"
        )
        ctk.CTkLabel(
            inner, text=taxa_str,
            font=ctk.CTkFont(size=10), text_color="#aaaaaa",
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 4), sticky="w")

        # Parcelas (apenas cr\u00e9dito)
        if self._tipo_cartao == "credito":
            parc_row = ctk.CTkFrame(inner, fg_color="transparent")
            parc_row.grid(row=3, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="ew")
            parc_row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                parc_row, text="Parcelas:",
                font=ctk.CTkFont(size=12), text_color="#555555",
            ).grid(row=0, column=0, padx=(0, 8), sticky="w")

            opcoes = [f"{n}x" for n in range(1, 13)]
            self.opt_parcelas = ctk.CTkOptionMenu(
                parc_row, values=opcoes, width=80, height=28,
                font=ctk.CTkFont(size=12),
                command=self._selecionar_parcelas,
            )
            self.opt_parcelas.set(f"{self._parcelas}x")
            self.opt_parcelas.grid(row=0, column=1, sticky="w")

            # Valor da parcela
            subtotal     = sum(item["subtotal"] for item in self._carrinho)
            desconto_val = round(subtotal * self._desconto_pct / 100, 2)
            total        = round(subtotal - desconto_val, 2)
            vp = total / self._parcelas if self._parcelas > 0 else total

            self.lbl_valor_parcela = ctk.CTkLabel(
                inner,
                text=f"Valor da Parcela: {formatar_moeda(vp)}",
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#1f6aa5",
            )
            self.lbl_valor_parcela.grid(
                row=4, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w"
            )
        else:
            ctk.CTkFrame(inner, fg_color="transparent", height=8).grid(row=3, column=0)

    def _selecionar_tipo_cartao(self, tipo: str):
        """Alterna D\u00e9bito / Cr\u00e9dito e reconstr\u00f3i o painel de cart\u00e3o."""
        self._tipo_cartao = tipo
        if tipo == "debito":
            self._parcelas = 1
        self._mostrar_painel_pagamento()

    def _atualizar_cores_tipo_cartao(self):
        """Destaca o tipo de cart\u00e3o ativo (D\u00e9bito ou Cr\u00e9dito)."""
        if not hasattr(self, "btn_debito"):
            return
        debito_ativo = (self._tipo_cartao == "debito")
        self.btn_debito.configure(
            fg_color="#2e7d32" if debito_ativo else "#3a9adf",
            hover_color="#1b5e20" if debito_ativo else "#2a7abf",
        )
        self.btn_credito.configure(
            fg_color="#3a9adf" if debito_ativo else "#2e7d32",
            hover_color="#2a7abf" if debito_ativo else "#1b5e20",
        )

    def _selecionar_parcelas(self, valor: str):
        """Atualiza parcelas e reconstr\u00f3i o painel para exibir taxa e valor da parcela."""
        try:
            self._parcelas = int(valor.replace("x", ""))
        except ValueError:
            self._parcelas = 1
        self._mostrar_painel_pagamento()
        self._atualizar_resumo()

    # ------------------------------------------------------------------
    # Fase 2: finalizar, limpar, imprimir
    # ------------------------------------------------------------------
    def _finalizar_compra(self):
        """Valida o carrinho e registra a venda no banco de dados."""
        if not self._carrinho:
            messagebox.showwarning("Aten\u00e7\u00e3o", "O carrinho est\u00e1 vazio.")
            return

        if self._forma_pagamento == "a_prazo" and not self._cliente_selecionado:
            messagebox.showwarning("Aten\u00e7\u00e3o", "Selecione um cliente para venda a prazo.")
            return

        cliente_id = self._cliente_selecionado["id"] if self._cliente_selecionado else None

        # Nome avulso — captura o texto digitado quando estava em modo sem cadastro
        nome_avulso: str | None = None
        if self._modo_sem_cadastro:
            nome_avulso = self.entry_cliente_busca.get().strip() or None

        if self._forma_pagamento == "cartao":
            taxa = (
                _TAXA_DEBITO
                if self._tipo_cartao == "debito"
                else _TAXAS_CREDITO.get(self._parcelas, 0.0)
            )
        else:
            taxa = 0.0

        ok, resultado = finalizar_venda(
            itens_carrinho=self._carrinho,
            cliente_id=cliente_id,
            forma_pagamento=self._forma_pagamento,
            desconto_pct=self._desconto_pct,
            taxa_cartao=taxa,
            parcelas=self._parcelas,
            nome_avulso=nome_avulso,
        )

        if not ok:
            messagebox.showerror("Erro ao finalizar", resultado)
            return

        self._ultima_venda_id = resultado
        self._venda_finalizada = True

        # Limpa o carrinho e reseta estado
        self._carrinho.clear()
        self._cliente_selecionado = None
        self._modo_sem_cadastro = False
        self._desconto_pct = 0.0
        self._parcelas = 1
        self._forma_pagamento = "dinheiro"
        self.entry_desconto.delete(0, "end")
        self.frame_cli_sel.grid_remove()
        self._restaurar_entry_cliente()
        self.entry_cliente_busca.delete(0, "end")
        self._recarregar_carrinho()
        self._atualizar_cores_forma()
        self._atualizar_cor_sem_cadastro()
        self._mostrar_painel_pagamento()

        # Troca botão Limpar → Imprimir Recibo
        self.btn_limpar_imprimir.configure(
            text="🖨️  Imprimir Recibo",
            fg_color="#1f6aa5", hover_color="#104a85",
            command=self._imprimir_recibo,
        )

        # Reativa o painel temporariamente para o usuário poder imprimir
        # Após 10 segundos, trava novamente se o carrinho ainda estiver vazio
        self._toggle_resumo(True)
        self.after(15_000, self._bloquear_se_vazio)

        messagebox.showinfo("Venda Finalizada", f"Venda #{resultado} registrada com sucesso!")

    def _bloquear_se_vazio(self):
        """Trava o Resumo do Pedido se o carrinho ainda estiver vazio (chamado 10s após venda)."""
        if not self._carrinho:
            self._toggle_resumo(False)

    def _imprimir_recibo(self):
        """Stub: impress\u00e3o de recibo (implementar nas pr\u00f3ximas etapas)."""
        messagebox.showinfo(
            "Em breve",
            "A impress\u00e3o de recibo ser\u00e1 implementada nas pr\u00f3ximas etapas.",
        )

    def _acao_limpar_ou_imprimir(self):
        """A\u00e7\u00e3o padr\u00e3o do bot\u00e3o inferior: limpa o carrinho com confirma\u00e7\u00e3o."""
        if not messagebox.askyesno("Limpar Carrinho", "Deseja remover todos os itens do carrinho?"):
            return
        self._limpar_carrinho()
        self._venda_finalizada = False
        self._ultima_venda_id = None
        self._desconto_pct    = 0.0
        self.entry_desconto.delete(0, "end")
        # Restaura bot\u00e3o
        self.btn_limpar_imprimir.configure(
            text="\ud83d\uddd1\ufe0f  Limpar Carrinho",
            fg_color="#888888", hover_color="#666666",
            command=self._acao_limpar_ou_imprimir,
        )
        self._atualizar_resumo()


# ------------------------------------------------------------------
# Popup: editar item do carrinho
# ------------------------------------------------------------------

class _EditarItemForm(ctk.CTkToplevel):
    """Janela modal para editar quantidade e preço unitário de um item no carrinho."""

    def __init__(self, parent, item: dict, on_salvar):
        super().__init__(parent)
        self._item      = item
        self._on_salvar = on_salvar

        self.title("Editar Item do Carrinho")
        self.geometry("330x205")
        self.resizable(False, False)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        # Quantidade
        ctk.CTkLabel(
            frame, text="Quantidade *",
            font=ctk.CTkFont(size=13), text_color="#333333",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_qtd = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
        )
        self.entry_qtd.insert(0, str(item["quantidade"]))
        self.entry_qtd.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        # Preço unitário
        ctk.CTkLabel(
            frame, text="Preço Unit. (R$) *",
            font=ctk.CTkFont(size=13), text_color="#333333",
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.entry_preco = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
        )
        self.entry_preco.insert(0, f"{item['preco_unitario']:.2f}".replace(".", ","))
        self.entry_preco.grid(row=1, column=1, sticky="ew")

        # Botões
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")

        ctk.CTkButton(
            btns, text="Cancelar", width=100, height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btns, text="Salvar", width=100, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1)

        self.after(100, self.lift)

    def _salvar(self):
        # Valida quantidade
        try:
            qtd = int(self.entry_qtd.get().strip())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Erro", "Informe uma quantidade válida maior que zero.", parent=self
            )
            return

        # Valida preço
        preco_str = self.entry_preco.get().strip().replace(",", ".")
        try:
            preco = float(preco_str)
            if preco <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Erro", "Informe um preço válido maior que zero.", parent=self
            )
            return

        self._item["quantidade"]     = qtd
        self._item["preco_unitario"] = preco
        self._item["subtotal"]       = round(qtd * preco, 2)

        self._on_salvar()
        self.destroy()
