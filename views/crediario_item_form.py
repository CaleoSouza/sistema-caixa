"""
crediario_item_form.py - Formulário popup para adicionar/editar item no crediário.
Exibido como CTkToplevel (modal) a partir da tela de detalhe do cliente.
"""

import logging
from datetime import date
import customtkinter as ctk
from tkinter import messagebox

from models.crediario_model import inserir_item, atualizar_item, listar_itens

log = logging.getLogger(__name__)


class CrediaroItemForm(ctk.CTkToplevel):
    """
    Janela modal para adicionar ou editar um item no crediário do cliente.
    Campos: Produto/Descrição, Data, Quantidade, Preço Unit. e Total (calculado).
    """

    def __init__(self, parent, cliente_id: int, item_id: int = None, on_salvar=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.item_id    = item_id
        self.on_salvar  = on_salvar

        titulo = "Editar Item do Crediário" if item_id else "Adicionar Item ao Crediário"
        self.title(titulo)
        self.geometry("430x340")
        self.resizable(False, False)
        self.grab_set()   # bloqueia a janela pai enquanto este popup estiver aberto

        self.grid_columnconfigure(0, weight=1)

        self._construir_ui()

        if self.item_id:
            self._preencher_dados()

        self.after(100, self.lift)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _construir_ui(self):
        # Campo produto
        ctk.CTkLabel(self, text="Produto / Descrição *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, padx=20, pady=(20, 4), sticky="w")
        self.entry_produto = ctk.CTkEntry(
            self, height=36, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=13), placeholder_text="Apenas para Serviços e Mão de Obra.",
        )
        self.entry_produto.grid(row=1, column=0, padx=20, sticky="ew")

        # Data, Quantidade e Preço na mesma linha
        frame_linha = ctk.CTkFrame(self, fg_color="transparent")
        frame_linha.grid(row=2, column=0, padx=20, pady=(14, 0), sticky="ew")
        frame_linha.grid_columnconfigure((0, 1, 2), weight=1)

        # Data
        ctk.CTkLabel(frame_linha, text="Data *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_data = ctk.CTkEntry(
            frame_linha, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            placeholder_text="DD/MM/AAAA",
        )
        self.entry_data.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_data.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        # Quantidade
        ctk.CTkLabel(frame_linha, text="Qtd. *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=1, sticky="w", pady=(0, 4))
        self.entry_qtd = ctk.CTkEntry(
            frame_linha, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
        )
        self.entry_qtd.insert(0, "1")
        self.entry_qtd.grid(row=1, column=1, padx=(0, 8), sticky="ew")
        self.entry_qtd.bind("<KeyRelease>", self._calcular_total)

        # Preço unitário
        ctk.CTkLabel(frame_linha, text="Preço Unit. (R$) *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=2, sticky="w", pady=(0, 4))
        self.entry_preco = ctk.CTkEntry(
            frame_linha, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            placeholder_text="0,00",
        )
        self.entry_preco.grid(row=1, column=2, sticky="ew")
        self.entry_preco.bind("<KeyRelease>", self._calcular_total)

        # Total calculado
        frame_total = ctk.CTkFrame(self, fg_color="transparent")
        frame_total.grid(row=3, column=0, padx=20, pady=(12, 0), sticky="w")

        ctk.CTkLabel(frame_total, text="Total:",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#555555").grid(row=0, column=0)
        self.lbl_total = ctk.CTkLabel(
            frame_total, text="R$ 0,00",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#1f6aa5")
        self.lbl_total.grid(row=0, column=1, padx=(10, 0))

        # Botões
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.grid(row=4, column=0, padx=20, pady=20, sticky="e")

        ctk.CTkButton(
            frame_btns, text="Cancelar", width=110, height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            frame_btns, text="Salvar", width=110, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Preenchimento no modo edição
    # ------------------------------------------------------------------
    def _preencher_dados(self):
        itens = listar_itens(self.cliente_id)
        item = next((i for i in itens if i["id"] == self.item_id), None)
        if not item:
            return

        self.entry_produto.insert(0, item["produto_nome"])
        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, item["data"])
        self.entry_qtd.delete(0, "end")
        self.entry_qtd.insert(0, str(item["quantidade"]))
        self.entry_preco.delete(0, "end")
        self.entry_preco.insert(0, f"{item['preco_unitario']:.2f}".replace(".", ","))
        self._calcular_total()

    # ------------------------------------------------------------------
    # Cálculo automático do total
    # ------------------------------------------------------------------
    def _calcular_total(self, event=None):
        try:
            qtd   = int(self.entry_qtd.get().strip() or 0)
            preco = float(self.entry_preco.get().strip().replace(",", ".") or 0)
            total = qtd * preco
            fmt   = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.lbl_total.configure(text=f"R$ {fmt}")
        except (ValueError, TypeError):
            self.lbl_total.configure(text="R$ 0,00")

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------
    def _salvar(self):
        produto = self.entry_produto.get().strip()
        data    = self.entry_data.get().strip()

        if not produto:
            messagebox.showerror("Erro", "Produto/Descrição é obrigatório.", parent=self)
            return
        if not data:
            messagebox.showerror("Erro", "Data é obrigatória.", parent=self)
            return
        try:
            qtd   = int(self.entry_qtd.get().strip())
            preco = float(self.entry_preco.get().strip().replace(",", "."))
            if qtd <= 0 or preco < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade e preço devem ser valores válidos.", parent=self)
            return

        dados = {
            "cliente_id":    self.cliente_id,
            "produto_nome":  produto,
            "data":          data,
            "quantidade":    qtd,
            "preco_unitario": preco,
            "total":         qtd * preco,
        }

        if self.item_id:
            atualizar_item(self.item_id, dados)
        else:
            inserir_item(dados)

        if self.on_salvar:
            self.on_salvar()
        self.destroy()
