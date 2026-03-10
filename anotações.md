# Anotações do Projeto - Sistema Caixa

Desenvolvedor: Caléo Souza Santos
Repositório: https://github.com/CaleoSouza/sistema-caixa

--------------------

## ✅ O que foi feito

### Etapa 1 - Base (concluída em 08/03/2026)
- [x] Definição da estrutura de pastas do projeto
- [x] Criação do repositório no GitHub (CaleoSouza/sistema-caixa)
- [x] `.gitignore` configurado (ignora banco de dados, venv, build, imagens de upload)
- [x] `database.py` — conexão SQLite + criação de todas as tabelas:
      - configuracoes, produtos, clientes, vendas, itens_venda
- [x] `main.py` — janela principal com detecção de resolução (HD/Full HD) e sidebar
- [x] `views/home_view.py` — dashboard com logo, nome da empresa e 3 cards:
      - Crediário (clientes em atraso)
      - Produtos (baixo estoque)
      - Vendas (total do dia)
- [x] `utils.py` — funções de formatação padrão brasileiro:
      - Moeda: R$ 1.234,50
      - Data: dd/mm/aaaa
      - Data e hora: dd/mm/aaaa HH:MM
      - CPF: 000.000.000-00
      - Telefone: (00) 00000-0000

### Polimentos UX - Produtos (09/03/2026)
- [x] Linhas da tabela de produtos completamente clicáveis (cursor hand2, hover sublinhado no nome)
- [x] Botão "Menu" da sidebar clicável → retorna para HomeView com efeito hover azul
- [x] Cards "Estoque Baixo" e "Próximo a Vencer (30 dias)" clicáveis como filtros:
      - Toggle: clicar no card ativo remove o filtro
      - Card ativo fica com fundo amarelo #fff3cd
      - Badge na barra de busca indica filtro ativo com instrução de remoção
      - Digitar na busca limpa o filtro de card automaticamente
      - Funções adicionadas: listar_estoque_baixo(), listar_proximos_vencer() (model) e obter_estoque_baixo(), obter_proximos_vencer() (controller)
- [x] Card "Produtos" da HomeView clicável → abre lista de produtos com filtro estoque_baixo ativo
      - Apenas o card Produtos tem ação; Crediário e Vendas permanecem estáticos
      - Efeito hover azul claro #f0f7ff em todo o card
- [x] ProdutosView aceita filtro_inicial como parâmetro para abrir já filtrado
- [x] Busca de produtos por leitor de código de barras funciona nativamente (KeyRelease captura a leitura; campo codigo_barras está no WHERE da query)

### Ajustes pós-Etapa 1 (09/03/2026)
- [x] Ícones dos botões da sidebar: mantidos como emojis Unicode (Bootstrap Icons descartado — requer lib Cairo não disponível no Windows)
- [x] Cards do Dashboard em Full HD corrigidos: removido weight da row dos cards para não crescerem verticalmente
- [x] Rodapé "Sistema desenvolvido por" fixado na parte inferior com linha espaçadora flexível (row com weight=1)
- [x] Logo da empresa: carrega `imagens/outros/souza.png` (PNG transparente, redimensionado proporcionalmente para 110x110 com Pillow); fallback para placeholder verde se imagem não existir

### Etapa 2a - Produtos / Listagem (concluída em 09/03/2026)
- [x] `models/produto_model.py` — CRUD completo no SQLite (listar, buscar, inserir, atualizar, excluir lógica, resumo)
- [x] `controllers/produto_controller.py` — validação, cálculo de status do estoque (sem_estoque, estoque_baixo, em_estoque, estoque_alto)
- [x] `views/produtos_view.py` — tela de listagem com:
      - Título com ícone + botão "Adicionar Produto"
      - Busca em tempo real (KeyRelease)
      - Tabela scrollável com colunas: ID, Nome, Quantidade, Preço, Total, Status, Ações
      - Status colorido: Estoque Alto (verde), Em estoque (preto), Estoque baixo (laranja), Sem estoque (vermelho)
      - Botões de editar (✏️) e excluir (🗑️) por linha com confirmação
      - 5 cards de resumo na parte inferior: Total de Produtos, Itens em Estoque, Valor Total do Estoque, Estoque Baixo, Próximo a Vencer

--------------------

### Etapa 2 - Produtos
- [ ] `models/produto_model.py` — consultas ao banco (CRUD)
- [ ] `controllers/produto_controller.py` — lógica de negócio
- [x] `views/produtos_view.py` — tela de listagem (concluída na Etapa 2a)

### Etapa 2b - Produtos / Formulário (concluída em 09/03/2026)
- [x] `views/produto_form.py` — formulário em-janela (CTkFrame, não CTkToplevel):
      - Campos: Nome, Quantidade, Preço Venda, Fornecedor (col esq); Data Validade, Categoria, Descrição (col centro); Código Barras + Gerar EAN-13, Imagem (col dir)
      - Upload de imagem salva em imagens/produtos/
      - Modo edição: pré-preenche com dados do produto
      - Após salvar: callback on_voltar retorna para a listagem
- [x] `database.py` atualizado: colunas fornecedor e data_validade adicionadas via _migrar_tabelas() (ALTER TABLE)
- [x] Geração de código EAN-13 com prefixo 789 (padrão brasileiro) e verificação de unicidade
- [x] `views/produto_detalhe.py` — tela de detalhe em-janela:
      - Cabeçalho: ← Voltar | nome do produto | ✏️ Editar | 🗑️ Excluir
      - Card esquerdo: imagem do produto ou placeholder
      - Card direito: todos os campos em grid + badge de status colorido + campo descrição
- [x] Tabela de listagem com larguras fixas por coluna (COLUNAS_TABELA) garantindo alinhamento perfeito entre cabeçalho e linhas
- [x] 20 produtos de teste inseridos via script para validação da interface

### Etapa 2b - Produtos / Formulário (próxima)
- [ ] `views/produto_form.py` (modal/janela separada) com:
      - Campos: Nome, Descrição, Categoria, Preço de Venda, Preço de Custo, Quantidade, Estoque Mínimo, Código de Barras
      - Upload de imagem do produto (salvar em imagens/produtos/)
      - Botão Salvar e Cancelar
      - Modo edição: pré-preenche os campos com os dados do produto selecionado
      - Após salvar: volta para a listagem e recarrega a tabela

### Etapa 2c - Produtos / Código de Barras
      - Geração de código de barras por produto
      - Consulta por código de barras na tela de Carrinho

### Etapa 3 - Clientes
- [ ] `models/cliente_model.py`
- [ ] `controllers/cliente_controller.py`
- [ ] `views/clientes_view.py` — CRUD + upload de foto

### Etapa 4 - Carrinho
- [ ] `models/venda_model.py`
- [ ] `controllers/venda_controller.py`
- [ ] `views/carrinho_view.py` — registrar venda, desconto, baixa de estoque automática

### Etapa 5 - Relatórios
- [ ] `views/relatorios_view.py` — relatórios de vendas, produtos e clientes

### Etapa 6 - Configurações
- [ ] `views/configuracoes_view.py` — nome da empresa, logo, backup do banco de dados

### Final
- [ ] Substituir placeholder verde pelo logo real da empresa (CS_logo.png)
- [ ] Ícone da janela (CS_logo.ico)
- [ ] Testes finais em HD e Full HD
- [ ] Build com Pyinstaller (gerar executável .exe)
- [ ] Remover ícones Bootstrap não utilizados

--------------------

## 💡 Ideias e observações

- Usar `utils.py` em todas as views para garantir padrão brasileiro
- Código de barras: biblioteca `python-barcode` para geração (a avaliar)
- Na tela Carrinho, permitir busca de produto por código de barras (leitura de leitor físico)
- Crediário: cliente com `tem_crediario = 1` e `debito_atual > 0` aparece como "em atraso" no dashboard
- Estoque mínimo por produto: campo `estoque_minimo` na tabela produtos (padrão = 5 unidades)
- Imagens de produtos e clientes são salvas na pasta local e o caminho fica registrado no banco
- Logo do sistema: usar `imagens/outros/souza.png` como referência; futuro logo real pode substituir esse arquivo com o mesmo nome

--------------------

## 🐛 Problemas encontrados e resolvidos

- Arquivo `nul` criado acidentalmente no primeiro mkdir via cmd — removido manualmente
- Comando `python` não reconhecido no bash do Windows — usar `py` (Windows Launcher)
- Bootstrap Icons SVG: biblioteca cairosvg requer libcairo-2.dll no Windows (não disponível) — descartado, ficamos com emojis Unicode
- Cards do Dashboard cresciam em Full HD — corrigido removendo `weight=1` da linha dos cards e usando `sticky="ew"` no lugar de `"nsew"`

--------------------
