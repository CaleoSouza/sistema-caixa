"""
cliente_form.py - Formulário de cadastro e edição de Cliente.
Exibido dentro da janela principal (CTkFrame), seguindo o padrão da Etapa 2.
Campos: Nome, CPF, Telefone, Email, Cidade, Endereço, Foto, Crediário.
"""

import logging
import customtkinter as ctk
from tkinter import messagebox, filedialog

from controllers.cliente_controller import (
    obter_por_id,
    salvar,
    salvar_foto_cliente,
    excluir_foto_cliente,
    PASTA_FOTOS_CLIENTES,
)
from utils import desformatar_moeda
from PIL import Image
import os

log = logging.getLogger(__name__)

# Tamanho do preview da foto
_PREVIEW_SIZE = (180, 180)


class ClienteForm(ctk.CTkFrame):
    """
    Tela de formulário de cliente — substitui a listagem na área de conteúdo.
    """

    def __init__(self, parent, controller, cliente_id: int = None, on_voltar=None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)

        self.controller   = controller
        self.cliente_id   = cliente_id
        self.on_voltar    = on_voltar
        self._foto_origem: str | None = None   # caminho temporário escolhido
        self._foto_atual:  str | None = None   # nome do arquivo já salvo no banco

        # Layout: título | painel (expande) | botões
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_ui()

        if self.cliente_id:
            self._preencher_dados()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------
    def _construir_ui(self):
        titulo = "✏️  Editar Cliente" if self.cliente_id else "+ Adicionar Novo Cliente"

        ctk.CTkLabel(
            self,
            text=titulo,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, padx=30, pady=(24, 10), sticky="w")

        # Painel central com scroll vertical
        painel = ctk.CTkScrollableFrame(self, fg_color="#d9d9d9", corner_radius=12)
        painel.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="nsew")
        painel.grid_columnconfigure((0, 1, 2), weight=1)

        self._criar_coluna_esquerda(painel)
        self._criar_coluna_central(painel)
        self._criar_coluna_direita(painel)

        self._criar_botoes()

    # ------------------------------------------------------------------
    # Coluna esquerda: Nome, CPF, Telefone, Email
    # ------------------------------------------------------------------
    def _criar_coluna_esquerda(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=0, padx=(20, 10), pady=16, sticky="nsew")
        col.grid_columnconfigure(0, weight=1)

        # Nome
        ctk.CTkLabel(col, text="Nome completo *",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_nome = ctk.CTkEntry(col, height=36, fg_color="white",
                                       border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_nome.grid(row=1, column=0, sticky="ew")

        # CPF
        ctk.CTkLabel(col, text="CPF",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=2, column=0, sticky="w", pady=(14, 4))
        self.entry_cpf = ctk.CTkEntry(col, height=36, fg_color="white",
                                      border_color="#cccccc", font=ctk.CTkFont(size=13),
                                      placeholder_text="000.000.000-00")
        self.entry_cpf.grid(row=3, column=0, sticky="ew")

        # Telefone
        ctk.CTkLabel(col, text="Telefone",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=4, column=0, sticky="w", pady=(14, 4))
        self.entry_telefone = ctk.CTkEntry(col, height=36, fg_color="white",
                                           border_color="#cccccc", font=ctk.CTkFont(size=13),
                                           placeholder_text="(48) 99999-9999")
        self.entry_telefone.grid(row=5, column=0, sticky="ew")

        # E-mail
        ctk.CTkLabel(col, text="E-mail",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=6, column=0, sticky="w", pady=(14, 4))
        self.entry_email = ctk.CTkEntry(col, height=36, fg_color="white",
                                        border_color="#cccccc", font=ctk.CTkFont(size=13),
                                        placeholder_text="email@exemplo.com")
        self.entry_email.grid(row=7, column=0, sticky="ew")

        # Data de Nascimento
        ctk.CTkLabel(col, text="Data de Nascimento",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=8, column=0, sticky="w", pady=(14, 4))
        self.entry_data_nasc = ctk.CTkEntry(col, height=36, fg_color="white",
                                            border_color="#cccccc", font=ctk.CTkFont(size=13),
                                            placeholder_text="DD/MM/AAAA")
        self.entry_data_nasc.grid(row=9, column=0, sticky="ew")

    # ------------------------------------------------------------------
    # Coluna central: Cidade, Endereço
    # ------------------------------------------------------------------
    def _criar_coluna_central(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=1, padx=10, pady=16, sticky="nsew")
        col.grid_columnconfigure(0, weight=1)
        col.grid_rowconfigure(3, weight=0)

        # Cidade
        ctk.CTkLabel(col, text="Cidade",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_cidade = ctk.CTkEntry(col, height=36, fg_color="white",
                                         border_color="#cccccc", font=ctk.CTkFont(size=13),
                                         placeholder_text="Ex: Jacinto Machado")
        self.entry_cidade.grid(row=1, column=0, sticky="ew")

        # Endereço
        ctk.CTkLabel(col, text="Endereço",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=2, column=0, sticky="w", pady=(14, 4))
        self.text_endereco = ctk.CTkTextbox(
            col, fg_color="white", border_width=1,
            border_color="#cccccc", font=ctk.CTkFont(size=13),
            corner_radius=8, height=100,
        )
        self.text_endereco.grid(row=3, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Coluna direita: Foto + Crediário
    # ------------------------------------------------------------------
    def _criar_coluna_direita(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=2, padx=(10, 20), pady=16, sticky="nsew")
        col.grid_columnconfigure(0, weight=1)

        # --- Foto do cliente ---
        ctk.CTkLabel(col, text="Foto do Cliente",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.frame_foto = ctk.CTkFrame(
            col, fg_color="white", border_width=1, border_color="#cccccc",
            corner_radius=8, width=200, height=160,
        )
        self.frame_foto.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.frame_foto.grid_propagate(False)
        self.frame_foto.grid_columnconfigure(0, weight=1)
        self.frame_foto.grid_rowconfigure(0, weight=1)

        self.lbl_preview = ctk.CTkLabel(
            self.frame_foto, text="Sem foto",
            text_color="#bbbbbb", font=ctk.CTkFont(size=13))
        self.lbl_preview.grid(row=0, column=0)

        frame_btn_foto = ctk.CTkFrame(col, fg_color="transparent")
        frame_btn_foto.grid(row=2, column=0, columnspan=2, sticky="e", pady=(6, 0))

        ctk.CTkButton(
            frame_btn_foto, text="Adicionar", width=90, height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._escolher_foto,
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            frame_btn_foto, text="Excluir", width=80, height=30,
            fg_color="#e53935", hover_color="#c62828",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._excluir_foto,
        ).grid(row=0, column=1)

        ctk.CTkLabel(col, text="Imagem tamanho máximo 2mb",
                     font=ctk.CTkFont(size=10), text_color="#888888").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # --- Seção de Crediário ---
        ctk.CTkLabel(col, text="Crediário",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#333333").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(20, 8))

        # Switch: tem crediário?
        frame_switch = ctk.CTkFrame(col, fg_color="transparent")
        frame_switch.grid(row=5, column=0, columnspan=2, sticky="w")

        ctk.CTkLabel(frame_switch, text="Possui crediário",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, padx=(0, 10))

        self.var_crediario = ctk.BooleanVar(value=False)
        self.switch_crediario = ctk.CTkSwitch(
            frame_switch, text="", variable=self.var_crediario,
            command=self._toggle_crediario,
        )
        self.switch_crediario.grid(row=0, column=1)

        # Limite de crédito
        ctk.CTkLabel(col, text="Limite de Crédito (R$)",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.entry_limite = ctk.CTkEntry(col, height=36, fg_color="white",
                                         border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_limite.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.entry_limite.insert(0, "0,00")

        # Débito atual
        ctk.CTkLabel(col, text="Débito Atual (R$)",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.entry_debito = ctk.CTkEntry(col, height=36, fg_color="white",
                                          border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_debito.grid(row=9, column=0, columnspan=2, sticky="ew")
        self.entry_debito.insert(0, "0,00")

        # Estado inicial dos campos de crediário
        self._toggle_crediario()

    # ------------------------------------------------------------------
    # Botões Cancelar / Salvar
    # ------------------------------------------------------------------
    def _criar_botoes(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=30, pady=16, sticky="e")

        ctk.CTkButton(
            frame, text="Cancelar", width=130, height=38,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._voltar,
        ).grid(row=0, column=0, padx=(0, 10))

        texto_btn = "Salvar" if self.cliente_id else "Adicionar"
        ctk.CTkButton(
            frame, text=texto_btn, width=130, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Preencher campos ao editar
    # ------------------------------------------------------------------
    def _preencher_dados(self):
        cliente = obter_por_id(self.cliente_id)
        if not cliente:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            self._voltar()
            return

        self._set_entry(self.entry_nome,      cliente.get("nome", ""))
        self._set_entry(self.entry_cpf,       cliente.get("cpf") or "")
        self._set_entry(self.entry_telefone,  cliente.get("telefone") or "")
        self._set_entry(self.entry_email,     cliente.get("email") or "")
        self._set_entry(self.entry_cidade,    cliente.get("cidade") or "")
        self._set_entry(self.entry_data_nasc, cliente.get("data_nascimento") or "")

        endereco = cliente.get("endereco") or ""
        if endereco:
            self.text_endereco.insert("1.0", endereco)

        # Crediário
        tem = bool(cliente.get("tem_crediario", 0))
        self.var_crediario.set(tem)
        self._toggle_crediario()

        limite = cliente.get("limite_credito", 0.0) or 0.0
        debito = cliente.get("debito_atual", 0.0) or 0.0
        self._set_entry(self.entry_limite, f"{limite:.2f}".replace(".", ","))
        self._set_entry(self.entry_debito, f"{debito:.2f}".replace(".", ","))

        # Foto
        self._foto_atual = cliente.get("foto")
        if self._foto_atual:
            self._exibir_foto(os.path.join(PASTA_FOTOS_CLIENTES, self._foto_atual))

    # ------------------------------------------------------------------
    # Toggle crediário: habilita ou desabilita os campos
    # ------------------------------------------------------------------
    def _toggle_crediario(self):
        ativo = self.var_crediario.get()
        estado = "normal" if ativo else "disabled"
        cor_borda = "#cccccc" if ativo else "#e8e8e8"
        self.entry_limite.configure(state=estado, border_color=cor_borda)
        self.entry_debito.configure(state=estado, border_color=cor_borda)

    # ------------------------------------------------------------------
    # Foto: escolher e exibir
    # ------------------------------------------------------------------
    def _escolher_foto(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar foto do cliente",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp")],
        )
        if not caminho:
            return
        self._foto_origem = caminho
        self._exibir_foto(caminho)

    def _exibir_foto(self, caminho: str):
        try:
            img = Image.open(caminho)
            img.thumbnail(_PREVIEW_SIZE, Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
            self.lbl_preview.configure(image=ctk_img, text="")
            self.lbl_preview._image = ctk_img
        except Exception:
            self.lbl_preview.configure(image=None, text="Sem foto")

    def _excluir_foto(self):
        # Remove o arquivo do disco se já estava salvo
        if self._foto_atual:
            excluir_foto_cliente(self._foto_atual)
            self._foto_atual = None
        # Descarta também seleção pendente (ainda não salva)
        self._foto_origem = None
        self.lbl_preview.configure(image=None, text="Sem foto")

    # ------------------------------------------------------------------
    # Salvar dados
    # ------------------------------------------------------------------
    def _salvar(self):
        nome        = self.entry_nome.get().strip()
        cpf         = self.entry_cpf.get().strip()
        telefone    = self.entry_telefone.get().strip()
        email       = self.entry_email.get().strip()
        cidade      = self.entry_cidade.get().strip()
        endereco    = self.text_endereco.get("1.0", "end").strip()
        tem_cred    = self.var_crediario.get()
        limite      = desformatar_moeda(self.entry_limite.get()) if tem_cred else 0.0
        debito      = desformatar_moeda(self.entry_debito.get()) if tem_cred else 0.0

        # Processa foto se uma nova foi selecionada
        foto_nome = self._foto_atual
        if self._foto_origem:
            foto_nome = salvar_foto_cliente(self._foto_origem, self._foto_atual)

        # Se excluiu a foto sem nova seleção
        if not self._foto_origem and not self.lbl_preview.cget("text") == "Sem foto":
            pass  # mantém a foto atual
        elif not self._foto_origem:
            if self.lbl_preview.cget("text") == "Sem foto" and self._foto_atual:
                excluir_foto_cliente(self._foto_atual)
                foto_nome = None

        data_nasc = self.entry_data_nasc.get().strip()

        dados = {
            "nome":             nome,
            "cpf":              cpf or None,
            "telefone":         telefone or None,
            "email":            email or None,
            "cidade":           cidade or None,
            "endereco":         endereco or None,
            "foto":             foto_nome,
            "tem_crediario":    int(tem_cred),
            "limite_credito":   limite,
            "debito_atual":     debito,
            "data_nascimento":  data_nasc or None,
        }

        ok, msg = salvar(dados, self.cliente_id)
        if ok:
            messagebox.showinfo("Sucesso", msg)
            self._voltar()
        else:
            messagebox.showerror("Erro", msg)

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _set_entry(self, entry: ctk.CTkEntry, valor: str):
        entry.delete(0, "end")
        entry.insert(0, valor)

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()
