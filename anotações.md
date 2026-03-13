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

### Etapa 3 - Clientes (concluída em 10/03/2026)
- [x] `models/cliente_model.py` — CRUD completo:
      - listar_clientes(busca), listar_em_atraso(), buscar_por_id(), resumo_clientes()
      - inserir_cliente(), atualizar_cliente(), excluir_cliente() (lógica: ativo=0)
      - Campos: nome, cpf, telefone, email, cidade, endereco, foto, tem_crediario,
                limite_credito, debito_atual, data_nascimento
- [x] `controllers/cliente_controller.py` — lógica de negócio:
      - _calcular_status(): sem_debitos | em_dia | em_atraso
      - salvar_foto_cliente(), excluir_foto_cliente()
      - PASTA_FOTOS_CLIENTES = imagens/clientes/
- [x] `views/clientes_view.py` — listagem com:
      - Tabela: ID, Nome, Telefone, Cidade, Status, Ações
      - Busca em tempo real (nome, CPF, telefone, cidade)
      - Card "Clientes em Atraso" clicável como filtro toggle (fundo #fff0f0)
      - Badge de filtro ativo na barra de busca
      - 3 cards: Total de Clientes, Clientes em Dia, Clientes em Atraso
      - Coluna filler (weight=1) no cabeçalho e scroll_frame para evitar corte da coluna Ações
      - _truncar() com _MAX_CHARS por coluna para textos longos
- [x] `views/cliente_form.py` — formulário 3 colunas:
      - Esquerda: Nome*, CPF, Telefone, Email, Data de Nascimento (DD/MM/AAAA)
      - Centro: Cidade, Endereço (CTkTextbox)
      - Direita: Foto upload (preview), CTkSwitch "Possui crediário",
                 Limite de Crédito, Débito Atual (desabilitados se sem crediário)
- [x] `views/cliente_detalhe.py` — detalhe compacto:
      - Cabeçalho: ← Voltar | nome | ✏️ Editar | 🗑️ Excluir
      - Card esquerdo: foto ou placeholder 👤
      - Card direito: CPF, Telefone, E-mail, Nascimento, Cidade, Status badge,
                      Crediário condicional (Limite + Débito), Endereço
- [x] `database.py` — migração automática: cidade TEXT e data_nascimento TEXT na tabela clientes
- [x] `main.py` — botão Clientes conectado a ClientesView
- [x] `views/home_view.py` — card Crediário conectado a ClientesView com filtro_inicial="em_atraso"
- [x] Fix tabelas: coluna filler + _truncar() aplicados também em produtos_view.py
- [x] 10 clientes de teste inseridos para validação da interface

### Redesign cliente_detalhe.py — Crediário e Pagamentos (11/03/2026)
- [x] `database.py` — 2 novas tabelas:
      - `crediario_itens`: id, cliente_id, produto_nome, data, quantidade, preco_unitario, total, criado_em
      - `historico_pagamentos`: id, cliente_id, data, tipo, valor, criado_em (ambas com FK para clientes)
- [x] `models/crediario_model.py` — CRUD completo:
      - listar_itens(), inserir_item(), atualizar_item(), excluir_item()
      - listar_pagamentos(), inserir_pagamento(), atualizar_pagamento(), excluir_pagamento()
      - calcular_saldo() → max(0, Σitens - Σpagamentos)
      - _sincronizar_debito() → atualiza clientes.debito_atual automaticamente
- [x] `views/crediario_item_form.py` — CTkToplevel modal para adicionar/editar item:
      - Campos: Produto/Descrição, Data (padrão hoje), Qtd. (padrão 1), Preço Unit.
      - Total calculado automaticamente (KeyRelease: qtd × preço)
- [x] `views/pagamento_form.py` — CTkToplevel modal para registrar/editar pagamento:
      - Campos: Data (padrão hoje), Tipo (Dinheiro/Cartão/Pix/Transferência/Cheque), Valor
- [x] `views/cliente_detalhe.py` — reescrita completa com novo layout:
      - Painel esquerdo: foto 110×130 + CPF/Tel/Email/Nascimento/Cidade/Status ao lado +
        seção Crediário (Limite + Débito Atual atualizado dinamicamente) + Endereço
      - Painel direito: 2 cards com CTkScrollableFrame
        • Card "Crediário": tabela (ID, Produto, Data, Qtd., Preço, Total, Ações ✏️🗑️🖨️)
          botão "+ Item" + "🖨️ Imprimir Hist. Completo" (stub por enquanto)
        • Card "Histórico de Pagamento": tabela (Data, Tipo, Valor, Ações ✏️🗑️🖨️)
          + Saldo Devedor (verde=zerado / vermelho=devendo)
      - _atualizar_tudo() recarrega tabelas, saldo e débito ao salvar/excluir
      - Botões 🖨️ exibem "Em breve" — impressão real será Etapa 3 Fase 2

### Etapa 3 - Clientes
- [ ] `models/venda_model.py`
- [ ] `controllers/venda_controller.py`
- [ ] `views/carrinho_view.py` — registrar venda, desconto, baixa de estoque automática

### Etapa 4 - Carrinho (concluída em 11/03/2026)

#### Fase 1 — Painel esquerdo (Produtos + Carrinho)
- [x] `database.py` — tabela `vendas` recebeu `taxa_cartao REAL` e `parcelas INTEGER` via _migrar_tabelas()
- [x] `models/venda_model.py` — CRUD completo:
      - registrar_venda(dados, itens) com transação atômica
      - listar_vendas(limite) com LEFT JOIN clientes
      - listar_itens_venda(venda_id)
      - total_vendas_hoje(), quantidade_vendas_hoje()
- [x] `controllers/venda_controller.py` — lógica completa:
      - finalizar_venda(): valida estoque → registra → baixa estoque → crediário (se a_prazo)
      - Fix: separação das conexões SQLite (estoque commit+close antes de abrir crediário)
      - obter_vendas(), obter_itens_venda() para Relatórios
- [x] `views/carrinho_view.py` — Fase 1:
      - COLS_DISP e COLS_CARR com larguras ajustadas para HD e Full HD (uniform="painel")
      - Card "Produtos Disponíveis": busca em tempo real + leitor de código de barras (Enter → buscar_por_codigo_barras → adiciona direto ao carrinho)
      - Filtros: Todos (azul) / Promoção (laranja) / Pouco Estoque (vermelho) com contagens dinâmicas
      - Nomes truncados com "..." a partir de 18 caracteres para não cortar botões
      - Botão "+ Adic." adiciona ao carrinho; incrementa quantidade se já existir
      - Card "Itens no Carrinho": botões ✏️ (azul claro) e 🗑️ (vermelho claro) com cor visível
      - _EditarItemForm (CTkToplevel): edita quantidade e preço unitário

#### Fase 2 — Painel direito (Resumo do Pedido)
- [x] Painel direito com CTkScrollableFrame rolável + botões fixos na parte inferior
- [x] Totais: Subtotal + campo Desconto % + botão Aplicar + Total em destaque azul
- [x] Cliente: busca rápida (3 letras → dropdown CTkToplevel), clique fixa com faixa azul + botão ✕
      - Botão "Sem Cadastro" remove seleção
- [x] Forma de Pagamento: 4 botões toggle (Dinheiro / PIX / Cartão / Prazo)
      - Dinheiro / PIX: campo de valor + troco em tempo real (verde=troco, vermelho=faltam)
      - Prazo: sem campo de valor — exibe mensagem informativa com/sem cliente selecionado
      - Cartão: botões Débito / Crédito + dropdown parcelas 1x–12x + taxa interna (referência vendedor) + Valor da Parcela
- [x] Taxas de cartão: Débito 1,66%; Crédito de 2% (1x) a 13% (12x) — apenas referência interna
- [x] Botão "Finalizar Compra" (verde): valida → registra → limpa carrinho + reset completo do painel
- [x] Botão "Limpar Carrinho" → após finalizar vira "Imprimir Recibo" (stub Em breve)
- [x] Fix: database locked → conexões separadas para baixa de estoque e crediário

### Ajustes visuais Carrinho (12/03/2026)
- [x] Tabelas responsivas: COLS_DISP e COLS_CARR trocaram largura fixa (px) por peso relativo (weight)
      - Colunas configuram `grid_columnconfigure(i, weight=peso)` sem `width=` nos labels
      - Labels com `sticky="ew"` preenchem a célula proporcionalmente em qualquer resolução
- [x] Coluna "Ações" com largura fixa via `minsize=80` nos três frames (cabeçalho, scroll_produtos, scroll_carrinho)
      - Ajuste centralizado: procurar `minsize=80` no arquivo para testar tamanhos
- [x] Botão "+ Adic." com tamanho fixo `width=72` (sem sticky="ew")
- [x] Botões ✏️ e 🗑️ com `width=34` cada, sem sticky="ew" → compactos/quadradinhos
      - Removido `fa.grid_columnconfigure((0,1), weight=1)` que os forçava a esticar
- [x] Fix cantos arredondados do painel direito: CTkScrollableFrame com `corner_radius=12` e `padx=2, pady=(2,0)`

### Sessão 13/03/2026 — Correções e Melhorias

#### Fix: Card Crediário na Home (home_view.py)
- [x] `_obter_resumo()` usava SQL inline `debito_atual > 0` (retornava 10 — todos com débito)
- [x] Corrigido: usa `resumo_clientes().get("em_atraso", 0)` com regra dos 30 dias → retorna valor correto
- [x] Card "Estoque Baixo" também corrigido para usar `resumo_produtos().get("estoque_baixo", 0)` em vez de SQL inline
- Commit: e2f7215

#### Fix: Flag tem_crediario não ativado ao adicionar +Item (crediario_model.py)
- [x] `_sincronizar_debito()` não setava `tem_crediario=1` ao inserir primeiro item de cliente com flag=0
- [x] Corrigido: usa `CASE WHEN EXISTS(SELECT 1 FROM crediario_itens WHERE cliente_id=?) THEN 1 ELSE tem_crediario END`
- [x] Clientes criados com `tem_crediario=0` agora ativam o flag automaticamente ao receber o primeiro item
- Commit: 611251a

#### Seed: 15 novos clientes de teste (total: 35 clientes)
- [x] 5 sem crediário: Rafael, Sabrina, Thiago, Úrsula, Vinícius (IDs 16–20)
- [x] 5 em dia (item 03/03/2026 — 10 dias): Wesley, Ximena, Yago, Zélia, Anderson (IDs 21–25)
- [x] 5 em atraso (item 01/02/2026 — 40 dias): Beatriz, Cláudio, Daniela, Eduardo, Fabiana (IDs 26–30)
- Resultado final: 35 clientes | 16 em dia | 10 em atraso

#### Feat: Bloqueio de CPF duplicado (database.py + cliente_model.py + cliente_controller.py)
- [x] Índice UNIQUE parcial no SQLite: `CREATE UNIQUE INDEX idx_clientes_cpf_unico ON clientes(cpf) WHERE cpf IS NOT NULL AND cpf != ''`
- [x] `buscar_por_cpf(cpf, excluir_id=None)` adicionada ao model — exclui próprio ID no modo edição
- [x] `_validar()` do controller verifica CPF antes de salvar; mensagem exibe nome + ID do cliente existente
- [x] 5 CPFs duplicados removidos do banco de dados
- Commit: d671a73

#### Feat: Regras fixas de estoque (produto_controller.py + produto_model.py)
- [x] `_calcular_status()` — lógica nova sem `estoque_minimo` dinâmico:
      0 → `sem_estoque` | 1–4 → `estoque_baixo` | 5–25 → `em_estoque` | 26+ → `estoque_alto`
- [x] `listar_estoque_baixo()` e `resumo_produtos()` atualizados: `WHERE quantidade <= 4` (inclui sem estoque)
- [x] Card "Estoque Baixo" na Home soma sem_estoque + estoque_baixo via `resumo_produtos()`
- Commit: 8cb1fa5

#### Fix: Dropdown busca cliente no Carrinho (carrinho_view.py)
- [x] Bug: dropdown aparecia abaixo dos botões de pagamento ao digitar mais de 3 letras
- [x] Tentativa 1 — `CTkToplevel` + `overrideredirect`: z-order instável, janela desaparecia
- [x] Tentativa 2 — `CTkFrame` + `place()`: `ValueError` — CTkFrame não aceita width/height no `place()` (devem ir no construtor)
- [x] Tentativa 3 — frame com parent root + `place()`: offset errado causado pelo `CTkScrollableFrame`
- [x] Solução final: `tk.Toplevel` puro + `wm_overrideredirect(True)` + coordenadas absolutas via `winfo_rootx()/winfo_rooty()` + `attributes("-topmost", True)`
- [x] `import tkinter as tk` adicionado ao topo do arquivo
- Commits: b0084f2, 130880d, 975f3e1, c371c2d, 9354c88

--------------------

### Etapa 5 - Despesas (concluída em 12/03/2026)
- [x] `database.py` — tabela `despesas` adicionada (id, descricao, data, responsavel, valor, forma_pagamento, status, criado_em)
- [x] `models/despesa_model.py` — CRUD completo:
      - listar_despesas(busca, mes, ano, status) com filtros combinados
      - buscar_por_id(), inserir_despesa(), atualizar_despesa(), excluir_despesa()
      - resumo_por_mes() → totais agrupados por status (pago, agendado, em_aberto)
- [x] `controllers/despesa_controller.py` — lógica de negócio:
      - obter_lista(), obter_resumo(), salvar(), remover(), obter_por_id()
      - STATUS_LABELS: pago | agendado | em_aberto
      - FORMAS_PAGAMENTO: Dinheiro, PIX, Boleto, Cartão, Transferência, Anotado
- [x] `views/despesa_form.py` — popup modal CTkToplevel para nova/editar despesa:
      - Campos: Descrição, Data (padrão hoje), Responsável, Valor, Forma de Pagamento, Status
      - Modo edição: pré-preenche todos os campos
      - geometry("420x520") para exibir todos os campos corretamente
- [x] `views/despesas_view.py` — tela completa:
      - Painel esquerdo: tabela com colunas Descrição, Data, Responsável, Valor, Pagamento, Status (colorido), Ações (✏️ 🗑️)
      - Filtros: busca por texto + dropdown Mês + dropdown Status
      - Botão “+ Adicionar Nova Despesa” e “🖨️ Imprimir Despesas” (stub)
      - Painel direito: 4 cards com seletor de mês individual cada:
        • Total de Despesas (Mês) — cor preta
        • Total de Despesas (Agendado) — cor laranja
        • Total de Despesas (Em Aberto) — cor vermelha
        • Total de Despesas (Pago) — cor verde
- [x] `main.py` — botão Despesas adicionado na sidebar entre Clientes e Relatórios

### Etapa 6 - Relatórios
- [ ] `views/relatorios_view.py` — relatórios de vendas, produtos e clientes

### Etapa 7 - Configurações
- [ ] `views/configuracoes_view.py` — nome da empresa, logo, backup do banco de dados

### Final
- [ ] Substituir placeholder verde pelo logo real da empresa (CS_logo.png)
- [ ] Ícone da janela (CS_logo.ico)
- [ ] Testes finais em HD e Full HD
- [ ] Build com Pyinstaller (gerar executável .exe)
- [ ] Remover ícones Bootstrap não utilizados

--------------------

## 💡 Ideias e observações

- **REGRA FUTURA — Integração Carrinho → Crediário:** ao finalizar uma venda no carrinho
  com forma de pagamento "A prazo" (crediário), cada item da venda deve ser automaticamente
  inserido na tabela `crediario_itens` do cliente selecionado, chamando `inserir_item()` do
  `crediario_model.py`. Isso sincroniza o débito do cliente automaticamente via `_sincronizar_debito()`.
  - O campo `produto_nome` receberá o nome do produto vendido
  - O campo `data` receberá a data da venda
  - O campo `quantidade`, `preco_unitario` e `total` vêm direto do item do carrinho
  - O cliente deve ter `tem_crediario = 1` para que a venda a prazo seja permitida

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
- Janela "Registrar Pagamento" cortava botões — corrigido: `geometry("380x300")`
- Ícones de emoji em botões não apareciam bem — corrigido com `text_color="#000000"` explícito

--------------------

## 📐 Padrões de UI estabelecidos (referência para novas telas)

### Botões de ações em tabelas (✏️ 🗑️ 🖨️)
- Sempre `text_color="#000000"` para emojis ficarem visíveis
- Sem `sticky="ew"` — tamanho fixo, não esticar
- Tamanhos: `width=34, height=26` (tabelas grandes) / `width=26, height=24` (tabelas compactas)
- `fg_color="transparent"` com hover colorido:
  - Editar  ✏️ → `hover_color="#e0e0e0"`
  - Excluir 🗑️ → `hover_color="#fde8e8"`
  - Imprimir 🖨️ → `hover_color="#e3f2fd"`

### Tabelas responsivas
- Colunas de dados: `grid_columnconfigure(i, weight=peso)` — sem `width=` nos CTkLabel
- Labels com `sticky="ew"` para preencherem a célula proporcionalmente
- Coluna "Ações": `weight=0, minsize=80` — largura fixa, não cresce
- Cabeçalho fixo e scroll_frame devem ter o mesmo padrão de colunas

### CTkScrollableFrame dentro de card arredondado
- Usar `corner_radius=12` + `padx=2, pady=(2,0)` para preservar os cantos do card pai

### Etapa 5 - Despesas (concluída em 12/03/2026)
- [x] `database.py` — tabela `despesas` adicionada: id, descricao, data (DD/MM/AAAA), responsavel, valor, forma_pagamento, status, criado_em
- [x] `models/despesa_model.py` — CRUD completo:
      - listar_despesas(busca, mes, ano, status): filtra via substr(data, 4, 2) e substr(data, 7, 4)
      - buscar_por_id(), inserir_despesa(), atualizar_despesa(), excluir_despesa()
      - resumo_por_mes(mes, ano) → {total_mes, total_agendado, total_em_aberto, total_pago}
- [x] `controllers/despesa_controller.py`:
      - obter_lista(), obter_resumo(), salvar(), remover(), obter_por_id()
      - STATUS_LABELS = {"pago": "Pago", "agendado": "Agendado", "em_aberto": "Em Aberto"}
      - FORMAS_PAGAMENTO = ["Dinheiro", "PIX", "Boleto", "Cartão", "Transferência", "Anotado"]
- [x] `views/despesa_form.py` — CTkToplevel modal 420×520:
      - Campos: Descrição, Data (padrão hoje), Responsável, Valor, Forma de Pagamento, Status
      - Modo edição: pré-preenche com dados da despesa selecionada
- [x] `views/despesas_view.py` — tela completa:
      - Painel esquerdo: tabela com colunas (Descrição, Data, Responsável, Valor, Pagamento, Status, Ações)
      - Filtros: busca em tempo real + seletor de mês
      - Status colorido: pago=#2e7d32 | agendado=#d97706 | em_aberto=#e53935
      - Painel direito: 4 cards (Total do Mês, Agendado, Em Aberto, Pago) com seletores individuais de mês
      - Painel direito convertido para CTkScrollableFrame (scroll em telas menores)
- [x] `main.py` — DespesasView importada e botão "💸 Despesas" adicionado à sidebar

### Etapa 5b - Despesas Automáticas (concluída em 13/03/2026)
- [x] `database.py` — nova tabela `despesas_automaticas`: id, descricao, dia_mes, responsavel, valor, forma_pagamento, criado_em
      - Migração: coluna `auto_origem_id` adicionada à tabela `despesas` para rastrear origem automática
- [x] `models/despesa_model.py` — CRUD automático:
      - listar_despesas_auto(), buscar_auto_por_id(), inserir_despesa_auto(), atualizar_despesa_auto(), excluir_despesa_auto()
      - gerar_despesas_mes(mes, ano): insere despesas na tabela principal se ainda não existir no mês (anti-duplicata via auto_origem_id)
      - Ajusta dia para não ultrapassar o último dia do mês (ex: dia 31 em fevereiro vira dia 28)
- [x] `controllers/despesa_controller.py` — funções auto:
      - obter_lista_auto(), obter_auto_por_id(), salvar_auto(), remover_auto()
      - gerar_despesas_mes_atual(): chama gerar_despesas_mes com mês/ano atual
- [x] `views/despesa_auto_form.py` — novo CTkToplevel modal 420×460:
      - Título: "Nova Despesa Automática" / "Editar Despesa Automática"
      - Campo "Dia (1-31) — todo mês" no lugar de data completa
      - Campos: Descrição, Dia do mês, Responsável, Valor, Forma de Pagamento
      - Aviso informativo: "Esta despesa será lançada automaticamente todo mês"
- [x] `views/despesas_view.py` — card "Despesas Automáticas (fixas)" no painel direito:
      - Botão "+ Criar Novo" abre DespesaAutoForm
      - Mini-tabela com CTkScrollableFrame (Descrição | Valor | Ações ✏️🗑️)
      - Ao abrir a tela: gera automaticamente os lançamentos do mês atual que ainda não existem
      - Ao salvar nova auto: regenera o mês atual e recarrega tabela + cards
- [x] Fix: `AttributeError _criar_card_automaticas` — métodos ausentes por falha de replace; corrigidos na mesma sessão
- [x] Fix: alinhamento de colunas na tabela de despesas — cabeçalho movido para dentro do CTkScrollableFrame (row=0), dados a partir de row=1; elimina desalinhamento causado pela scrollbar interna (~16px)

### Etapa 5c - Refatoração de tabelas — todas as views (concluída em 13/03/2026)
- [x] Padrão aplicado a TODAS as tabelas do sistema: cabeçalho renderizado dentro do `CTkScrollableFrame` como row=0, dados a partir de `enumerate(..., start=1)`
- [x] `views/produtos_view.py`: removido frame `cabecalho` separado; `grid_rowconfigure(2)` → `(1)`, scroll passa para row=1; cabeçalho adicionado em `carregar_produtos()` com `fg_color="#f0f0f0"`
- [x] `views/clientes_view.py`: mesma mudança que produtos_view
- [x] `views/carrinho_view.py`: `_criar_cabecalho_tabela()` substituído por `_inserir_cabecalho(scroll, colunas)` que renderiza dentro do scroll; `card.grid_rowconfigure(4→3)` em card_produtos, `(2→1)` em card_carrinho; scrolls movidos uma row acima; lambdas do carrinho usam `idx` (0-based) para indexar `self._carrinho`
- [x] `views/cliente_detalhe.py`: mesmo padrão; `_criar_cabecalho_tabela()` substituído por `_inserir_cabecalho(scroll, colunas)`; `card.grid_rowconfigure(2→1)` em ambos os cards; separador/saldo ajustados de row=3,4 para row=2,3
- [x] Commit: `d9a04fb`

### Etapa 6 - Relatórios / Fase 1 (concluída em 12/03/2026)
- [x] `views/relatorios_view.py` — tela criada com 2 cards:
      - Card "Fechamento do Dia": tkcalendar DateEntry (locale="pt_BR", date_pattern="dd/MM/yyyy") + botão "🔍 Ver" + Resumo Rápido (qtd vendas + valor total do dia)
      - Card "Fechamento do Mês": CTkOptionMenu meses em PT + CTkEntry ano + botão "🔍 Ver" + Resumo Rápido do mês
      - _ver_dia() e _ver_mes() com placeholder "Em breve" — tabela detalhada será implementada na Fase 2
      - Funções internas: _resumo_dia(data_iso) e _resumo_mes(mes, ano) consultam a tabela vendas diretamente
      - tkcalendar 1.6.1 já instalado; fallback para CTkEntry se import falhar
- [x] `main.py` — RelatoriosView importada e botão "📊 Relatórios" adicionado à sidebar
- [ ] Fase 2: tabelas detalhadas de vendas por dia e por mês (implementar em sessão futura)

### Cores e tema
- Tema: claro (`ctk.set_appearance_mode("light")`)
- Azul primário: `#1f6aa5` | hover: `#104a85`
- Azul secundário (inativo): `#3a9adf` | hover: `#2a7abf`
- Verde confirmação: `#2e7d32` | hover: `#1b5e20`
- Cinza neutro: `#888888` | hover: `#666666`
- Vermelho destrutivo: `#e53935` | hover: `#c62828`

### Layout de tela principal
- Split 50/50 com `grid_columnconfigure(0|1, weight=1, uniform="painel")`
- Título da tela: `CTkFont(size=26, weight="bold")`, `text_color="#1f6aa5"`
- Cards com `fg_color="white", corner_radius=12`
- Fundo geral: `fg_color="#e8e8e8"`

--------------------
