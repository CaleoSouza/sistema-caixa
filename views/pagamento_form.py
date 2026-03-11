"""
pagamento_form.py - Formulário popup para registrar/editar pagamento no histórico.
Exibido como CTkToplevel (modal) a partir da tela de detalhe do cliente.
"""

import logging
from datetime import date
import customtkinter as ctk
from tkinter import messagebox

from models.crediario_model import inserir_pagamento, atualizar_pagamento, listar_pagamentos

log = logging.getLogger(__name__)

TIPOS_PAGAMENTO = ["Dinheiro", "Cartão", "Pix", "Transferência", "Cheque"]


class PagamentoForm(ctk.CTkToplevel):
    """
    Janela modal para registrar ou editar um pagamento do cliente.
    Campos: Data, Tipo (OptionMenu) e Valor.
    """

    def __init__(self, parent, cliente_id: int, pag_id: int = None, on_salvar=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.pag_id     = pag_id
        self.on_salvar  = on_salvar

        titulo = "Editar Pagamento" if pag_id else "Registrar Pagamento"
        self.title(titulo)
        self.geometry("380x240")
        self.resizable(False, False)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self._construir_ui()

        if self.pag_id:
            self._preencher_dados()

        self.after(100, self.lift)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _construir_ui(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        # Data
        ctk.CTkLabel(frame, text="Data *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_data = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            placeholder_text="DD/MM/AAAA",
        )
        self.entry_data.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_data.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        # Tipo
        ctk.CTkLabel(frame, text="Tipo *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=1, sticky="w", pady=(0, 4))
        self.optmenu_tipo = ctk.CTkOptionMenu(
            frame, values=TIPOS_PAGAMENTO,
            font=ctk.CTkFont(size=13), height=36,
        )
        self.optmenu_tipo.set("Dinheiro")
        self.optmenu_tipo.grid(row=1, column=1, sticky="ew")

        # Valor
        ctk.CTkLabel(frame, text="Valor (R$) *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(14, 4))
        self.entry_valor = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            placeholder_text="0,00",
        )
        self.entry_valor.grid(row=3, column=0, columnspan=2, sticky="ew")

        # Botões
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")

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
        pags = listar_pagamentos(self.cliente_id)
        pag  = next((p for p in pags if p["id"] == self.pag_id), None)
        if not pag:
            return

        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, pag["data"])
        self.optmenu_tipo.set(pag["tipo"])
        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, f"{pag['valor']:.2f}".replace(".", ","))

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------
    def _salvar(self):
        data      = self.entry_data.get().strip()
        tipo      = self.optmenu_tipo.get()
        valor_str = self.entry_valor.get().strip().replace(",", ".")

        if not data:
            messagebox.showerror("Erro", "Data é obrigatória.", parent=self)
            return
        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Informe um valor válido maior que zero.", parent=self)
            return

        dados = {
            "cliente_id": self.cliente_id,
            "data":       data,
            "tipo":       tipo,
            "valor":      valor,
        }

        if self.pag_id:
            atualizar_pagamento(self.pag_id, dados)
        else:
            inserir_pagamento(dados)

        if self.on_salvar:
            self.on_salvar()
        self.destroy()
