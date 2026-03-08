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

--------------------

## 🔄 O que falta fazer

### Etapa 2 - Produtos
- [ ] `models/produto_model.py` — consultas ao banco (CRUD)
- [ ] `controllers/produto_controller.py` — lógica de negócio
- [ ] `views/produtos_view.py` — tela completa com:
      - Listagem de produtos em tabela
      - Formulário de cadastro/edição
      - Upload de imagem do produto
      - Controle de estoque
      - Geração de código de barras

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

--------------------

## 🐛 Problemas encontrados e resolvidos

- Arquivo `nul` criado acidentalmente no primeiro mkdir via cmd — removido manualmente
- Comando `python` não reconhecido no bash do Windows — usar `py` (Windows Launcher)

--------------------
