"""
produto_form.py - Formulário de cadastro e edição de Produto.
Modal que abre sobre a tela de listagem de produtos.
Campos: nome, data_validade, codigo_barras, quantidade, categoria,
        descricao, preco, fornecedor, imagem.
"""

import os
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image

from controllers.produto_controller import (
    obter_por_id,
    salvar,
    gerar_codigo_ean13,
    validar_ean13,
    salvar_imagem_produto,
    excluir_imagem_produto,
    PASTA_IMAGENS_PRODUTOS,
)
from utils import desformatar_moeda


# ------------------------------------------------------------------
# Helpers de data (formato brasileiro ↔ ISO)
# ------------------------------------------------------------------

def _br_para_iso(data_br: str) -> str:
    """'21/03/2026' → '2026-03-21'. Retorna '' se inválida."""
    data_br = data_br.strip()
    if not data_br:
        return ""
    partes = data_br.split("/")
    if len(partes) == 3 and all(p.isdigit() for p in partes):
        dia, mes, ano = partes
        if len(ano) == 4 and 1 <= int(mes) <= 12 and 1 <= int(dia) <= 31:
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
    return ""


def _iso_para_br(data_iso: str) -> str:
    """'2026-03-21' → '21/03/2026'. Retorna '' se nulo."""
    if not data_iso:
        return ""
    partes = data_iso.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return ""


class ProdutoForm(ctk.CTkFrame):
    """
    Tela de formulário de produto — substitui a listagem na área de conteúdo.
    Navegação de volta feita pelo callback on_voltar() (fornecido por ProdutosView).
    """

    def __init__(self, parent, controller, produto_id: int = None, on_voltar=None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)

        self.controller  = controller
        self.produto_id  = produto_id
        self.on_voltar   = on_voltar
        # Listas de 3 slots: índices 0, 1, 2 → foto 1, 2, 3
        self._imagem_origens: list[str | None] = [None, None, None]
        self._imagem_atuais:  list[str | None] = [None, None, None]

        # Layout: título (fixo) | painel (expande) | botões (fixo)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_ui()

        if self.produto_id:
            self._preencher_dados()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _construir_ui(self):
        titulo = "✏️  Editar Produto" if self.produto_id else "+ Adicionar Novo Produto"

        # Título
        ctk.CTkLabel(
            self,
            text=titulo,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, padx=30, pady=(24, 10), sticky="w")

        # Painel central com scroll — adapta a telas menores sem esmagar os campos
        painel = ctk.CTkScrollableFrame(self, fg_color="#d9d9d9", corner_radius=12)
        painel.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="nsew")
        painel.grid_columnconfigure(0, weight=1)
        painel.grid_columnconfigure(1, weight=1)

        self._criar_coluna_esquerda(painel)
        self._criar_coluna_direita(painel)

        # Botões de ação
        self._criar_botoes()

    # ------------------------------------------------------------------
    # Coluna esquerda: Nome, Quantidade, Preço, Fornecedor, Descrição
    # ------------------------------------------------------------------

    def _criar_coluna_esquerda(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=0, padx=(20, 10), pady=16, sticky="new")
        col.grid_columnconfigure(0, weight=1)

        # Nome do Produto
        ctk.CTkLabel(col, text="Nome do Produto",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_nome = ctk.CTkEntry(col, height=36, fg_color="white",
                                       border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_nome.grid(row=1, column=0, sticky="ew")

        # Quantidade
        ctk.CTkLabel(col, text="Quantidade",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=2, column=0, sticky="w", pady=(14, 4))
        self.entry_quantidade = ctk.CTkEntry(col, height=36, fg_color="white",
                                             border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_quantidade.grid(row=3, column=0, sticky="ew")
        self.entry_quantidade.insert(0, "0")

        # Preço de Venda
        ctk.CTkLabel(col, text="Preço (R$)",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=4, column=0, sticky="w", pady=(14, 4))
        self.entry_preco = ctk.CTkEntry(col, height=36, fg_color="white",
                                        border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_preco.grid(row=5, column=0, sticky="ew")
        self.entry_preco.insert(0, "0,00")

        # Fornecedor
        ctk.CTkLabel(col, text="Fornecedor",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=6, column=0, sticky="w", pady=(14, 4))
        self.entry_fornecedor = ctk.CTkEntry(col, height=36, fg_color="white",
                                             border_color="#cccccc", font=ctk.CTkFont(size=13))
        self.entry_fornecedor.grid(row=7, column=0, sticky="ew")

        # Descrição (expande para preencher o espaço restante)
        ctk.CTkLabel(col, text="Descrição",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=8, column=0, sticky="w", pady=(14, 4))
        self.text_descricao = ctk.CTkTextbox(col, height=160, fg_color="white", border_width=1,
                                             border_color="#cccccc", font=ctk.CTkFont(size=13),
                                             corner_radius=8)
        self.text_descricao.grid(row=9, column=0, sticky="ew")
        self.text_descricao.insert("1.0", "")

    # ------------------------------------------------------------------
    # Coluna direita: Data Validade, Categoria, Código de Barras, Imagem
    # ------------------------------------------------------------------

    def _criar_coluna_direita(self, pai):
        col = ctk.CTkFrame(pai, fg_color="transparent")
        col.grid(row=0, column=1, padx=(10, 20), pady=16, sticky="new")
        col.grid_columnconfigure(0, weight=1)

        # Data de Validade
        ctk.CTkLabel(col, text="Data de Validade",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_validade = ctk.CTkEntry(col, height=36, fg_color="white",
                                           border_color="#cccccc", font=ctk.CTkFont(size=13),
                                           placeholder_text="dd/mm/aaaa")
        self.entry_validade.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(col, text="Opcional - Para produtos perecíveis",
                     font=ctk.CTkFont(size=10), text_color="#888888").grid(
            row=2, column=0, sticky="w", pady=(2, 0))

        # Categoria
        ctk.CTkLabel(col, text="Categoria",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=3, column=0, sticky="w", pady=(14, 4))
        self.entry_categoria = ctk.CTkEntry(col, height=36, fg_color="white",
                                            border_color="#cccccc", font=ctk.CTkFont(size=13),
                                            placeholder_text="Ex: Bebidas, Alimentos")
        self.entry_categoria.grid(row=4, column=0, sticky="ew")

        # --- Código de Barras ---
        ctk.CTkLabel(col, text="Código de Barras",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=5, column=0, sticky="w", pady=(14, 4))

        frame_cod = ctk.CTkFrame(col, fg_color="transparent")
        frame_cod.grid(row=6, column=0, sticky="ew")
        frame_cod.grid_columnconfigure(0, weight=1)

        self.entry_codigo_barras = ctk.CTkEntry(
            frame_cod, height=36, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=13), placeholder_text="Passe o leitor aqui")
        self.entry_codigo_barras.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            frame_cod, text="Gerar", width=80, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._gerar_codigo_barras,
        ).grid(row=0, column=1)

        ctk.CTkLabel(col, text="Opcional - Gerado automaticamente se vazio",
                     font=ctk.CTkFont(size=10), text_color="#888888").grid(
            row=7, column=0, sticky="nw", pady=(2, 8))

        # --- Imagem do Produto (3 fotos opcionais) ---
        ctk.CTkLabel(col, text="Fotos do Produto (opcional, máx. 3)",
                     font=ctk.CTkFont(size=13), text_color="#333333").grid(
            row=8, column=0, sticky="w", pady=(4, 6))

        self._lbl_previews: list[ctk.CTkLabel] = []

        fotos_frame = ctk.CTkFrame(col, fg_color="transparent")
        fotos_frame.grid(row=9, column=0, sticky="ew")
        fotos_frame.grid_columnconfigure(0, weight=1)

        for idx in range(3):
            slot = ctk.CTkFrame(fotos_frame, fg_color="transparent")
            slot.grid(row=idx, column=0, pady=(0 if idx == 0 else 8, 0), sticky="ew")
            slot.grid_columnconfigure(1, weight=1)

            # Preview (coluna 0 — tamanho fixo)
            frame_prev = ctk.CTkFrame(
                slot, fg_color="white", border_width=1, border_color="#cccccc",
                corner_radius=8, width=130, height=90)
            frame_prev.grid(row=0, column=0, rowspan=2, sticky="ns")
            frame_prev.grid_propagate(False)
            frame_prev.grid_columnconfigure(0, weight=1)
            frame_prev.grid_rowconfigure(0, weight=1)

            lbl = ctk.CTkLabel(
                frame_prev, text=f"Foto {idx + 1}",
                text_color="#bbbbbb", font=ctk.CTkFont(size=11))
            lbl.grid(row=0, column=0)
            self._lbl_previews.append(lbl)

            # Label do slot (coluna 1)
            ctk.CTkLabel(
                slot, text=f"Foto {idx + 1}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#333333",
            ).grid(row=0, column=1, padx=(10, 0), sticky="sw")

            # Botões Adicionar / Excluir (coluna 1)
            fr_btn = ctk.CTkFrame(slot, fg_color="transparent")
            fr_btn.grid(row=1, column=1, padx=(10, 0), sticky="nw")

            ctk.CTkButton(
                fr_btn, text="Adicionar Foto", height=30, width=130,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda i=idx: self._escolher_imagem(i),
            ).grid(row=0, column=0, padx=(0, 6))

            ctk.CTkButton(
                fr_btn, text="Excluir", height=30, width=90,
                fg_color="#e53935", hover_color="#c62828",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda i=idx: self._excluir_imagem(i),
            ).grid(row=0, column=1)

        ctk.CTkLabel(col, text="Imagem tamanho máximo 1mb cada",
                     font=ctk.CTkFont(size=10), text_color="#888888").grid(
            row=10, column=0, sticky="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # Botões Cancelar / Adicionar (ou Salvar)
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

        texto_btn = "Salvar" if self.produto_id else "Adicionar"
        ctk.CTkButton(
            frame, text=texto_btn, width=130, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Preencher campos ao editar
    # ------------------------------------------------------------------

    def _preencher_dados(self):
        """Busca o produto no banco e preenche todos os campos."""
        produto = obter_por_id(self.produto_id)
        if not produto:
            messagebox.showerror("Erro", "Produto não encontrado.")
            self._voltar()
            return

        self._set_entry(self.entry_nome,           produto.get("nome", ""))
        self._set_entry(self.entry_quantidade,      str(produto.get("quantidade", 0)))
        self._set_entry(self.entry_preco,           f"{produto.get('preco', 0):.2f}".replace(".", ","))
        self._set_entry(self.entry_fornecedor,      produto.get("fornecedor") or "")
        self._set_entry(self.entry_validade,        _iso_para_br(produto.get("data_validade") or ""))
        self._set_entry(self.entry_categoria,       produto.get("categoria") or "")
        self._set_entry(self.entry_codigo_barras,   produto.get("codigo_barras") or "")

        descricao = produto.get("descricao") or ""
        self.text_descricao.delete("1.0", "end")
        self.text_descricao.insert("1.0", descricao)

        # Imagens existentes (3 slots)
        chaves = ["imagem", "imagem2", "imagem3"]
        for idx, chave in enumerate(chaves):
            nome = produto.get(chave) or None
            self._imagem_atuais[idx] = nome
            if nome:
                caminho = os.path.join(PASTA_IMAGENS_PRODUTOS, nome)
                self._mostrar_preview(caminho, idx)

    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, valor: str):
        entry.delete(0, "end")
        entry.insert(0, valor)

    # ------------------------------------------------------------------
    # Ações de imagem
    # ------------------------------------------------------------------

    def _escolher_imagem(self, slot: int = 0):
        """Abre diálogo para selecionar imagem do produto para o slot indicado."""
        caminho = filedialog.askopenfilename(
            title=f"Selecionar foto {slot + 1} do produto",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return

        if os.path.getsize(caminho) > 1 * 1024 * 1024:
            messagebox.showwarning(
                "Imagem muito grande",
                "A imagem selecionada excede 1 MB.\nPor favor escolha uma imagem menor.",
            )
            return

        self._imagem_origens[slot] = caminho
        self._mostrar_preview(caminho, slot)

    def _excluir_imagem(self, slot: int = 0):
        """Remove a imagem do slot indicado (apaga do disco se já estava salva)."""
        if self._imagem_atuais[slot]:
            excluir_imagem_produto(self._imagem_atuais[slot])
            self._imagem_atuais[slot] = None
        self._imagem_origens[slot] = None
        self._lbl_previews[slot].configure(image=None, text=f"Foto {slot + 1}")

    def _mostrar_preview(self, caminho: str, slot: int = 0):
        """Exibe miniatura da imagem no painel de preview do slot."""
        try:
            img = Image.open(caminho)
            img.thumbnail((130, 90), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
            self._lbl_previews[slot].configure(image=ctk_img, text="")
            self._lbl_previews[slot]._image = ctk_img
        except Exception:
            self._lbl_previews[slot].configure(image=None, text="Erro")

    # ------------------------------------------------------------------
    # Geração de código de barras
    # ------------------------------------------------------------------

    def _gerar_codigo_barras(self):
        """Gera um EAN-13 brasileiro e insere no campo."""
        try:
            codigo = gerar_codigo_ean13()
            self._set_entry(self.entry_codigo_barras, codigo)
        except RuntimeError as e:
            messagebox.showerror("Erro", str(e))

    # ------------------------------------------------------------------
    # Salvar produto
    # ------------------------------------------------------------------

    def _salvar(self):
        """Coleta, valida e persiste os dados do formulário."""

        # --- Coletar campos ---
        nome       = self.entry_nome.get().strip()
        fornecedor = self.entry_fornecedor.get().strip()
        categoria  = self.entry_categoria.get().strip()
        descricao  = self.text_descricao.get("1.0", "end").strip()
        codigo_barras = self.entry_codigo_barras.get().strip()

        # Quantidade
        try:
            quantidade = int(self.entry_quantidade.get().strip() or "0")
            if quantidade < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Campo inválido", "Quantidade deve ser um número inteiro positivo.")
            self.entry_quantidade.focus_set()
            return

        # Preço — aceita vírgula ou ponto como decimal
        try:
            preco_str = self.entry_preco.get().strip().replace(".", "").replace(",", ".")
            preco = float(preco_str)
            if preco < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Campo inválido", "Preço inválido. Use o formato: 9,99")
            self.entry_preco.focus_set()
            return

        # Data de validade — converte BR → ISO
        validade_br  = self.entry_validade.get().strip()
        data_validade = ""
        if validade_br:
            data_validade = _br_para_iso(validade_br)
            if not data_validade:
                messagebox.showwarning(
                    "Data inválida",
                    "Data de validade inválida.\nUse o formato: dd/mm/aaaa",
                )
                self.entry_validade.focus_set()
                return

        # Código de barras — se informado, deve ser EAN-13 válido
        if codigo_barras and not validar_ean13(codigo_barras):
            messagebox.showwarning(
                "Código inválido",
                "O código de barras deve ter 13 dígitos (EAN-13).\n"
                "Para gerar automaticamente, clique em 'Gerar'.",
            )
            self.entry_codigo_barras.focus_set()
            return

        # Se campo vazio, gerar automaticamente
        if not codigo_barras:
            try:
                codigo_barras = gerar_codigo_ean13()
            except RuntimeError as e:
                messagebox.showerror("Erro", str(e))
                return

        # --- Processar as 3 imagens ---
        chaves = ["imagem", "imagem2", "imagem3"]
        imagens_nomes: list[str | None] = []
        for idx in range(3):
            if self._imagem_origens[idx]:
                # Nova imagem selecionada — salva no disco
                nome_arq, msg_img = salvar_imagem_produto(
                    self._imagem_origens[idx],
                    nome_produto=nome,
                    produto_id=self.produto_id,
                    slot=idx + 1,
                )
                if nome_arq is None:
                    messagebox.showwarning(f"Foto {idx + 1}", msg_img)
                    return
                # Remove foto anterior diferente
                if self._imagem_atuais[idx] and self._imagem_atuais[idx] != nome_arq:
                    excluir_imagem_produto(self._imagem_atuais[idx])
                imagens_nomes.append(nome_arq)
            else:
                # Mantém ou deixa None (foi excluída)
                imagens_nomes.append(self._imagem_atuais[idx])

        # --- Montar dicionário e salvar ---
        dados = {
            "nome":           nome,
            "descricao":      descricao,
            "categoria":      categoria,
            "fornecedor":     fornecedor,
            "preco":          preco,
            "preco_custo":    0.0,
            "quantidade":     quantidade,
            "estoque_minimo": 5,
            "codigo_barras":  codigo_barras,
            "data_validade":  data_validade or None,
            "imagem":         imagens_nomes[0],
            "imagem2":        imagens_nomes[1],
            "imagem3":        imagens_nomes[2],
        }

        ok, msg = salvar(dados, self.produto_id)
        if ok:
            messagebox.showinfo("Sucesso", msg)
            self._voltar()
        else:
            messagebox.showerror("Erro ao salvar", msg)

    # ------------------------------------------------------------------
    # Navegação de volta
    # ------------------------------------------------------------------

    def _voltar(self):
        """Retorna para a tela de listagem de produtos."""
        if callable(self.on_voltar):
            self.on_voltar()
