"""
despesa_form.py - Popup modal para adicionar ou editar uma despesa.
"""

import datetime
import customtkinter as ctk
from tkinter import messagebox

from controllers.despesa_controller import salvar, STATUS_LABELS, FORMAS_PAGAMENTO

# Meses em português para exibição
_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


class DespesaForm(ctk.CTkToplevel):
    """
    Janela modal para adicionar ou editar uma despesa.
    - despesa: dict com dados para pré-preencher (modo edição) ou None (modo novo)
    - on_salvar: callback chamado após salvar com sucesso
    """

    def __init__(self, parent, despesa: dict | None, on_salvar):
        super().__init__(parent)
        self._despesa   = despesa
        self._on_salvar = on_salvar

        titulo = "Editar Despesa" if despesa else "Nova Despesa"
        self.title(titulo)
        self.geometry("420x520")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self.grid_columnconfigure(0, weight=1)
        self._construir_ui()

        if despesa:
            self._preencher(despesa)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _construir_ui(self):
        pad = {"padx": 20, "pady": (10, 0)}

        # Título interno
        ctk.CTkLabel(
            self,
            text="Editar Despesa" if self._despesa else "Nova Despesa",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        # Descrição
        ctk.CTkLabel(self, text="Descrição *", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=1, column=0, **pad, sticky="w")
        self.entry_descricao = ctk.CTkEntry(
            self, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="Ex: Aluguel, Fornecedor...",
        )
        self.entry_descricao.grid(row=2, column=0, padx=20, pady=(4, 0), sticky="ew")

        # Linha: Data + Responsável
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        linha.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(linha, text="Data *", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(linha, text="Responsável", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=1, sticky="w")

        hoje = datetime.date.today().strftime("%d/%m/%Y")
        self.entry_data = ctk.CTkEntry(
            linha, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="DD/MM/AAAA",
        )
        self.entry_data.insert(0, hoje)
        self.entry_data.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        self.entry_responsavel = ctk.CTkEntry(
            linha, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="Nome do responsável",
        )
        self.entry_responsavel.grid(row=1, column=1, sticky="ew")

        # Linha: Valor + Forma de Pagamento
        linha2 = ctk.CTkFrame(self, fg_color="transparent")
        linha2.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        linha2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(linha2, text="Valor (R$) *", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(linha2, text="Forma de Pagamento", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=1, sticky="w")

        self.entry_valor = ctk.CTkEntry(
            linha2, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="0,00",
        )
        self.entry_valor.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        self.opt_pagamento = ctk.CTkOptionMenu(
            linha2, values=FORMAS_PAGAMENTO, height=32,
            font=ctk.CTkFont(size=12),
        )
        self.opt_pagamento.set("Dinheiro")
        self.opt_pagamento.grid(row=1, column=1, sticky="ew")

        # Status
        ctk.CTkLabel(self, text="Status", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=5, column=0, **pad, sticky="w")
        self.opt_status = ctk.CTkOptionMenu(
            self, values=list(STATUS_LABELS.values()), height=32,
            font=ctk.CTkFont(size=12),
        )
        self.opt_status.set("Em Aberto")
        self.opt_status.grid(row=6, column=0, padx=20, pady=(4, 0), sticky="ew")

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=7, column=0, padx=20, pady=18, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="💾  Salvar", height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1, sticky="ew")

    # ------------------------------------------------------------------
    # Preenche campos no modo edição
    # ------------------------------------------------------------------
    def _preencher(self, d: dict):
        self.entry_descricao.delete(0, "end")
        self.entry_descricao.insert(0, d.get("descricao", ""))

        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, d.get("data", ""))

        self.entry_responsavel.delete(0, "end")
        self.entry_responsavel.insert(0, d.get("responsavel", "") or "")

        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, str(d.get("valor", "0")).replace(".", ","))

        forma = d.get("forma_pagamento", "Dinheiro")
        if forma in FORMAS_PAGAMENTO:
            self.opt_pagamento.set(forma)

        status_label = STATUS_LABELS.get(d.get("status", "em_aberto"), "Em Aberto")
        self.opt_status.set(status_label)

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------
    def _salvar(self):
        # Converte label do status de volta para chave interna
        label_para_chave = {v: k for k, v in STATUS_LABELS.items()}
        status_chave = label_para_chave.get(self.opt_status.get(), "em_aberto")

        dados = {
            "id":              self._despesa["id"] if self._despesa else None,
            "descricao":       self.entry_descricao.get(),
            "data":            self.entry_data.get(),
            "responsavel":     self.entry_responsavel.get(),
            "valor":           self.entry_valor.get(),
            "forma_pagamento": self.opt_pagamento.get(),
            "status":          status_chave,
        }

        ok, resultado = salvar(dados)
        if not ok:
            messagebox.showerror("Erro", resultado, parent=self)
            return

        self.destroy()
        self._on_salvar()
