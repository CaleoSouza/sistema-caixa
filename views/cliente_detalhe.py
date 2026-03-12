"""
cliente_detalhe.py - Tela de visualização detalhada de um Cliente.
Painel esquerdo: foto pequena, dados e crediário.
Painel direito: tabelas de itens do crediário e histórico de pagamentos.
"""

import os
import logging
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from controllers.cliente_controller import (
    obter_por_id,
    remover,
    PASTA_FOTOS_CLIENTES,
)
from models.crediario_model import (
    listar_itens,
    excluir_item,
    listar_pagamentos,
    excluir_pagamento,
    calcular_saldo,
)
from utils import formatar_moeda, formatar_cpf, formatar_telefone, formatar_data

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constantes de layout
# ------------------------------------------------------------------
_FOTO_SIZE = (110, 130)     # foto reduzida no painel esquerdo

# Status do crediário → (texto, cor_fundo, cor_texto)
STATUS_BADGE = {
    "sem_debitos": ("Sem débitos", "#f0f0f0", "#555555"),
    "em_dia":      ("Em dia",      "#e8f5e9", "#2e7d32"),
    "em_atraso":   ("Em atraso",   "#fde8e8", "#e53935"),
}

# Colunas da tabela de itens do crediário: (rótulo, largura px)
COLS_CRED = [
    ("ID", 38), ("Produto", 120), ("Data", 82),
    ("Qtd.", 42), ("Preço", 78), ("Total", 78), ("Ações", 92),
]

# Colunas da tabela de histórico de pagamentos
COLS_PAG = [("Data", 95), ("Tipo", 105), ("Valor", 92), ("Ações", 92)]


class ClienteDetalhe(ctk.CTkFrame):
    """
    Tela de detalhe de cliente com tabelas de crediário e pagamentos.
    """

    def __init__(self, parent, controller, cliente_id: int, on_voltar=None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)

        self.controller = controller
        self.cliente_id = cliente_id
        self.on_voltar  = on_voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)   # conteúdo estica verticalmente

        self.cliente = obter_por_id(cliente_id)
        if not self.cliente:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            self._voltar()
            return

        self._construir_ui()
        log.info("ClienteDetalhe carregado: id=%s", cliente_id)

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        c = self.cliente
        self._criar_cabecalho(c)

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        conteudo.grid_columnconfigure(0, weight=4)   # painel esquerdo
        conteudo.grid_columnconfigure(1, weight=5)   # painel direito
        conteudo.grid_rowconfigure(0, weight=1)

        self._criar_painel_esquerdo(conteudo, c)
        self._criar_painel_direito(conteudo)

    # ------------------------------------------------------------------
    # Cabeçalho: ← Voltar | 👤 Nome | Editar | Excluir
    # ------------------------------------------------------------------
    def _criar_cabecalho(self, c: dict):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame, text="← Voltar", width=100, height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._voltar,
        ).grid(row=0, column=0, padx=(0, 16))

        ctk.CTkLabel(
            frame, text=f"👤  {c['nome']}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            frame, text="✏️  Editar", width=106, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._editar,
        ).grid(row=0, column=2, padx=(8, 6))

        ctk.CTkButton(
            frame, text="🗑️  Excluir", width=106, height=36,
            fg_color="#e53935", hover_color="#c62828",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._excluir,
        ).grid(row=0, column=3)

    # ------------------------------------------------------------------
    # Painel esquerdo: foto + info + crediário + endereço
    # ------------------------------------------------------------------
    def _criar_painel_esquerdo(self, pai, c: dict):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        linha_card = 0

        # ---- Foto pequena + campos ao lado ----
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.grid(row=linha_card, column=0, padx=14, pady=(14, 8), sticky="ew")
        topo.grid_columnconfigure(1, weight=1)
        linha_card += 1

        # Moldura da foto
        foto_frame = ctk.CTkFrame(
            topo, fg_color="#f0f0f0", corner_radius=8,
            width=_FOTO_SIZE[0], height=_FOTO_SIZE[1],
        )
        foto_frame.grid(row=0, column=0, padx=(0, 12))
        foto_frame.grid_propagate(False)
        foto_frame.grid_columnconfigure(0, weight=1)
        foto_frame.grid_rowconfigure(0, weight=1)

        foto_nome = c.get("foto")
        if foto_nome:
            caminho = os.path.join(PASTA_FOTOS_CLIENTES, foto_nome)
            try:
                img = Image.open(caminho)
                img.thumbnail(_FOTO_SIZE, Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                lbl_foto = ctk.CTkLabel(foto_frame, image=ctk_img, text="")
                lbl_foto._image = ctk_img
                lbl_foto.grid(row=0, column=0)
            except Exception:
                ctk.CTkLabel(foto_frame, text="👤", font=ctk.CTkFont(size=30),
                             text_color="#cccccc").grid(row=0, column=0)
        else:
            ctk.CTkLabel(foto_frame, text="👤", font=ctk.CTkFont(size=30),
                         text_color="#cccccc").grid(row=0, column=0)

        # Campos ao lado da foto
        campos_frame = ctk.CTkFrame(topo, fg_color="transparent")
        campos_frame.grid(row=0, column=1, sticky="nsew")

        status = c.get("status_credito", "sem_debitos")
        badge_texto, badge_bg, badge_cor = STATUS_BADGE.get(
            status, ("—", "#f0f0f0", "#555555")
        )

        campos = [
            ("CPF",           formatar_cpf(c.get("cpf") or "") or "—"),
            ("Telefone",      formatar_telefone(c.get("telefone") or "") or "—"),
            ("E-mail",        c.get("email") or "—"),
            ("Nascimento",    c.get("data_nascimento") or "—"),
            ("Cidade",        c.get("cidade") or "—"),
            ("Cadastrado em", formatar_data(c.get("criado_em") or "") or "—"),
        ]

        for i, (rot, val) in enumerate(campos):
            ctk.CTkLabel(
                campos_frame, text=f"{rot}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#555555", anchor="w",
            ).grid(row=i, column=0, sticky="w", pady=1)
            ctk.CTkLabel(
                campos_frame, text=val,
                font=ctk.CTkFont(size=12), text_color="#1a1a1a", anchor="w",
            ).grid(row=i, column=1, padx=(6, 0), sticky="w", pady=1)

        # Badge de status
        ctk.CTkLabel(
            campos_frame, text="Status:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#555555", anchor="w",
        ).grid(row=len(campos), column=0, sticky="w", pady=(4, 0))
        badge = ctk.CTkFrame(campos_frame, fg_color=badge_bg, corner_radius=6)
        badge.grid(row=len(campos), column=1, padx=(6, 0), pady=(4, 0), sticky="w")
        ctk.CTkLabel(
            badge, text=badge_texto,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=badge_cor,
        ).grid(padx=8, pady=2)

        # ---- Separador ----
        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).grid(
            row=linha_card, column=0, padx=14, sticky="ew")
        linha_card += 1

        # ---- Seção de crediário ----
        if c.get("tem_crediario"):
            sec = ctk.CTkFrame(card, fg_color="transparent")
            sec.grid(row=linha_card, column=0, padx=14, pady=(10, 6), sticky="ew")
            sec.grid_columnconfigure(1, weight=1)
            linha_card += 1

            ctk.CTkLabel(
                sec, text="💳  Crediário",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1f6aa5",
            ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

            # Limite
            ctk.CTkLabel(
                sec, text="Limite:",
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#555555",
            ).grid(row=1, column=0, sticky="w", pady=1)
            ctk.CTkLabel(
                sec, text=formatar_moeda(c.get("limite_credito", 0)),
                font=ctk.CTkFont(size=12), text_color="#1a1a1a",
            ).grid(row=1, column=1, padx=(8, 0), sticky="w", pady=1)

            # Débito atual (referência armazenada para atualização dinâmica)
            ctk.CTkLabel(
                sec, text="Débito Atual:",
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#555555",
            ).grid(row=2, column=0, sticky="w", pady=1)
            cor_debito = "#e53935" if (c.get("debito_atual") or 0) > 0 else "#1a1a1a"
            self.lbl_debito = ctk.CTkLabel(
                sec, text=formatar_moeda(c.get("debito_atual", 0)),
                font=ctk.CTkFont(size=12, weight="bold"), text_color=cor_debito,
            )
            self.lbl_debito.grid(row=2, column=1, padx=(8, 0), sticky="w", pady=1)

        # ---- Endereço ----
        endereco = (c.get("endereco") or "").strip()
        if endereco:
            ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).grid(
                row=linha_card, column=0, padx=14, sticky="ew")
            linha_card += 1

            sec_end = ctk.CTkFrame(card, fg_color="transparent")
            sec_end.grid(row=linha_card, column=0, padx=14, pady=(8, 14), sticky="new")
            sec_end.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                sec_end, text="Endereço:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#555555", anchor="w",
            ).grid(row=0, column=0, sticky="w", pady=(0, 4))
            caixa = ctk.CTkTextbox(
                sec_end, height=55, fg_color="#f5f5f5",
                border_width=0, font=ctk.CTkFont(size=12),
                corner_radius=8, state="normal",
            )
            caixa.insert("1.0", endereco)
            caixa.configure(state="disabled")
            caixa.grid(row=1, column=0, sticky="ew")

    # ------------------------------------------------------------------
    # Painel direito: cards de crediário e pagamentos
    # ------------------------------------------------------------------
    def _criar_painel_direito(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew")
        col.grid_columnconfigure(0, weight=1)
        col.grid_rowconfigure(0, weight=3)   # card itens: maior
        col.grid_rowconfigure(1, weight=2)   # card pagamentos: menor

        self._criar_card_itens(col)
        self._criar_card_pagamentos(col)

    # -- Card: Itens do crediário --
    def _criar_card_itens(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, pady=(0, 8), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)   # scroll estica

        # Cabeçalho
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Crediário",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5",
        ).grid(row=0, column=0, sticky="w")

        frame_btns = ctk.CTkFrame(hdr, fg_color="transparent")
        frame_btns.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            frame_btns, text="+ Item", width=80, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._adicionar_item,
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            frame_btns, text="🖨️  Imprimir Hist. Completo", width=190, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._imprimir_completo,
        ).grid(row=0, column=1)

        # Cabeçalho fixo da tabela
        self._criar_cabecalho_tabela(card, COLS_CRED, row=1)

        # Área de rolagem dos itens
        self.scroll_itens = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_itens.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, larg) in enumerate(COLS_CRED):
            self.scroll_itens.grid_columnconfigure(i, minsize=larg, weight=0)
        self.scroll_itens.grid_columnconfigure(len(COLS_CRED), weight=1)

        self._recarregar_itens()

    # -- Card: Histórico de pagamentos --
    def _criar_card_pagamentos(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)   # scroll estica

        # Cabeçalho
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="Histórico de Pagamento",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr, text="+ Pagamento", width=110, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._adicionar_pagamento,
        ).grid(row=0, column=1, sticky="e")

        # Cabeçalho fixo da tabela
        self._criar_cabecalho_tabela(card, COLS_PAG, row=1)

        # Área de rolagem dos pagamentos
        self.scroll_pags = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_pags.grid(row=2, column=0, padx=8, pady=(0, 4), sticky="nsew")
        for i, (_, larg) in enumerate(COLS_PAG):
            self.scroll_pags.grid_columnconfigure(i, minsize=larg, weight=0)
        self.scroll_pags.grid_columnconfigure(len(COLS_PAG), weight=1)

        # Separador + Saldo Devedor
        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).grid(
            row=3, column=0, padx=12, pady=(4, 4), sticky="ew")

        frame_saldo = ctk.CTkFrame(card, fg_color="transparent")
        frame_saldo.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="e")

        ctk.CTkLabel(
            frame_saldo, text="Saldo Devedor: ",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#1a1a1a",
        ).grid(row=0, column=0)
        self.lbl_saldo_valor = ctk.CTkLabel(
            frame_saldo, text="R$ 0,00",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2e7d32",
        )
        self.lbl_saldo_valor.grid(row=0, column=1)

        self._recarregar_pagamentos()

    # ------------------------------------------------------------------
    # Utilitário: cabeçalho de tabela fixo
    # ------------------------------------------------------------------
    def _criar_cabecalho_tabela(self, pai, colunas: list, row: int):
        cab = ctk.CTkFrame(pai, fg_color="#f0f0f0", corner_radius=0, height=28)
        cab.grid(row=row, column=0, padx=8, sticky="ew")
        cab.grid_propagate(False)
        for i, (rot, larg) in enumerate(colunas):
            cab.grid_columnconfigure(i, minsize=larg, weight=0)
            ctk.CTkLabel(
                cab, text=rot,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#555555", width=larg, anchor="w",
            ).grid(row=0, column=i, padx=(6, 0), pady=2, sticky="w")
        cab.grid_columnconfigure(len(colunas), weight=1)

    # ------------------------------------------------------------------
    # Recarregamento das tabelas
    # ------------------------------------------------------------------
    def _recarregar_itens(self):
        for w in self.scroll_itens.winfo_children():
            w.destroy()

        itens = listar_itens(self.cliente_id)
        if not itens:
            ctk.CTkLabel(
                self.scroll_itens, text="Nenhum item no crediário.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=0, column=0, columnspan=len(COLS_CRED) + 1, pady=14)
            return

        for linha, item in enumerate(itens):
            dados_cols = [
                (f"#{item['id']:02d}",                  "#555555"),
                (item["produto_nome"],                   "#1a1a1a"),
                (item["data"],                           "#1a1a1a"),
                (str(item["quantidade"]),                "#1a1a1a"),
                (formatar_moeda(item["preco_unitario"]), "#1a1a1a"),
                (formatar_moeda(item["total"]),          "#1f6aa5"),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll_itens, text=texto,
                    font=ctk.CTkFont(size=12), text_color=cor,
                    width=COLS_CRED[col][1], anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="w")

            # Botões de ação da linha
            fa = ctk.CTkFrame(self.scroll_itens, fg_color="transparent")
            fa.grid(row=linha, column=6, padx=(2, 0), pady=2, sticky="w")

            ctk.CTkButton(
                fa, text="✏️", width=26, height=24,
                fg_color="transparent", hover_color="#e0e0e0",
                font=ctk.CTkFont(size=12), text_color="#000000",
                command=lambda iid=item["id"]: self._editar_item(iid),
            ).grid(row=0, column=0)
            ctk.CTkButton(
                fa, text="🗑️", width=26, height=24,
                fg_color="transparent", hover_color="#fde8e8",
                font=ctk.CTkFont(size=12), text_color="#000000",
                command=lambda iid=item["id"]: self._excluir_item(iid),
            ).grid(row=0, column=1)
            ctk.CTkButton(
                fa, text="🖨️", width=26, height=24,
                fg_color="transparent", hover_color="#e3f2fd",
                font=ctk.CTkFont(size=12), text_color="#000000",
                command=lambda iid=item["id"]: self._imprimir_item(iid),
            ).grid(row=0, column=2)

    def _recarregar_pagamentos(self):
        for w in self.scroll_pags.winfo_children():
            w.destroy()

        pags = listar_pagamentos(self.cliente_id)
        if not pags:
            ctk.CTkLabel(
                self.scroll_pags, text="Nenhum pagamento registrado.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=0, column=0, columnspan=len(COLS_PAG) + 1, pady=14)
        else:
            for linha, pag in enumerate(pags):
                dados_cols = [
                    (pag["data"],                   "#1a1a1a"),
                    (pag["tipo"],                   "#1a1a1a"),
                    (formatar_moeda(pag["valor"]),  "#2e7d32"),
                ]
                for col, (texto, cor) in enumerate(dados_cols):
                    ctk.CTkLabel(
                        self.scroll_pags, text=texto,
                        font=ctk.CTkFont(size=12), text_color=cor,
                        width=COLS_PAG[col][1], anchor="w",
                    ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="w")

                fa = ctk.CTkFrame(self.scroll_pags, fg_color="transparent")
                fa.grid(row=linha, column=3, padx=(2, 0), pady=2, sticky="w")

                ctk.CTkButton(
                    fa, text="✏️", width=26, height=24,
                    fg_color="transparent", hover_color="#e0e0e0",
                    font=ctk.CTkFont(size=12), text_color="#000000",
                    command=lambda pid=pag["id"]: self._editar_pagamento(pid),
                ).grid(row=0, column=0)
                ctk.CTkButton(
                    fa, text="🗑️", width=26, height=24,
                    fg_color="transparent", hover_color="#fde8e8",
                    font=ctk.CTkFont(size=12), text_color="#000000",
                    command=lambda pid=pag["id"]: self._excluir_pagamento(pid),
                ).grid(row=0, column=1)
                ctk.CTkButton(
                    fa, text="🖨️", width=26, height=24,
                    fg_color="transparent", hover_color="#e3f2fd",
                    font=ctk.CTkFont(size=12), text_color="#000000",
                    command=lambda pid=pag["id"]: self._imprimir_pagamento(pid),
                ).grid(row=0, column=2)

        # Atualiza o saldo devedor
        saldo = calcular_saldo(self.cliente_id)
        cor   = "#e53935" if saldo > 0 else "#2e7d32"
        self.lbl_saldo_valor.configure(text=formatar_moeda(saldo), text_color=cor)

    # ------------------------------------------------------------------
    # Atualização geral (chamada após qualquer operação de CRUD)
    # ------------------------------------------------------------------
    def _atualizar_tudo(self):
        """Recarrega tabelas, saldo e débito atual do cliente."""
        self.cliente = obter_por_id(self.cliente_id)
        self._recarregar_itens()
        self._recarregar_pagamentos()

        # Atualiza débito no painel esquerdo (se o label existir)
        if hasattr(self, "lbl_debito") and self.cliente:
            debito = self.cliente.get("debito_atual") or 0
            cor    = "#e53935" if debito > 0 else "#1a1a1a"
            self.lbl_debito.configure(text=formatar_moeda(debito), text_color=cor)

    # ------------------------------------------------------------------
    # Ações — Itens do crediário
    # ------------------------------------------------------------------
    def _adicionar_item(self):
        from views.crediario_item_form import CrediaroItemForm
        CrediaroItemForm(self, self.cliente_id, on_salvar=self._atualizar_tudo)

    def _editar_item(self, item_id: int):
        from views.crediario_item_form import CrediaroItemForm
        CrediaroItemForm(
            self, self.cliente_id, item_id=item_id, on_salvar=self._atualizar_tudo
        )

    def _excluir_item(self, item_id: int):
        if messagebox.askyesno("Confirmar", "Remover este item do crediário?"):
            excluir_item(item_id, self.cliente_id)
            self._atualizar_tudo()

    def _imprimir_item(self, item_id: int):
        messagebox.showinfo("Em breve", "A impressão por item será implementada em breve.")

    # ------------------------------------------------------------------
    # Ações — Histórico de pagamentos
    # ------------------------------------------------------------------
    def _adicionar_pagamento(self):
        from views.pagamento_form import PagamentoForm
        PagamentoForm(self, self.cliente_id, on_salvar=self._atualizar_tudo)

    def _editar_pagamento(self, pag_id: int):
        from views.pagamento_form import PagamentoForm
        PagamentoForm(
            self, self.cliente_id, pag_id=pag_id, on_salvar=self._atualizar_tudo
        )

    def _excluir_pagamento(self, pag_id: int):
        if messagebox.askyesno("Confirmar", "Remover este pagamento do histórico?"):
            excluir_pagamento(pag_id, self.cliente_id)
            self._atualizar_tudo()

    def _imprimir_pagamento(self, pag_id: int):
        messagebox.showinfo("Em breve", "A impressão individual será implementada em breve.")

    def _imprimir_completo(self):
        messagebox.showinfo("Em breve", "A impressão completa será implementada em breve.")

    # ------------------------------------------------------------------
    # Ações do cabeçalho (Editar / Excluir / Voltar)
    # ------------------------------------------------------------------
    def _editar(self):
        from views.cliente_form import ClienteForm

        def voltar_para_detalhe():
            self.controller.mostrar_tela(
                ClienteDetalhe,
                cliente_id=self.cliente_id,
                on_voltar=self.on_voltar,
            )

        self.controller.mostrar_tela(
            ClienteForm,
            cliente_id=self.cliente_id,
            on_voltar=voltar_para_detalhe,
        )

    def _excluir(self):
        resposta = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja remover o cliente '{self.cliente['nome']}'?\n"
            "Essa ação não pode ser desfeita.",
        )
        if resposta:
            ok, msg = remover(self.cliente_id)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self._voltar()
            else:
                messagebox.showerror("Erro", msg)

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()
        else:
            from views.clientes_view import ClientesView
            self.controller.mostrar_tela(ClientesView)
