# Meu painel de gastos pessoais

Dashboard em Python para acompanhar receitas e despesas a partir de um extrato CSV ou Excel. O projeto foi feito como peça de portfólio: interface interativa, gráficos, filtros, categorização por palavras-chave e exportação dos dados filtrados.

## Demonstração local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

O painel abre no navegador usando os dados de `exemplo_gastos.csv`. Envie seu próprio arquivo pela barra lateral para substituir os dados de demonstração.

## Publicar no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e entre com sua conta.
2. Conecte sua conta GitHub ao Streamlit Community Cloud.
3. Selecione o repositório `jotavea/painel-gastos-pessoais`, a branch `main` e o arquivo `app.py`.
4. Publique o app.

## Importação de dados

Envie CSV (separado por vírgulas ou ponto e vírgula) ou Excel (`.xlsx`/`.xls`). As colunas obrigatórias são:

| Campo | Nomes aceitos | Uso |
| --- | --- | --- |
| Data | `data` ou `date` | Data da transação, como `31/01/2026` |
| Valor | `valor` ou `amount` | Valor numérico da transação |
| Descrição | `descricao`, `descrição` ou `description` | Usada para sugerir categoria |
| Categoria | `categoria` ou `category` | Categoria existente, opcional |
| Tipo | `tipo` ou `type` | `despesa` ou `receita`, opcional |

Se a categoria estiver vazia, o app tenta sugeri-la usando palavras da descrição. Sem a coluna de tipo, valores negativos representam despesas e valores positivos representam receitas. Você pode baixar o CSV de exemplo diretamente no painel.

## Funcionalidades

- Indicadores de despesas, receitas, saldo e gasto diário médio
- Gráfico de gastos por categoria e comparação mensal de despesas e receitas
- Filtros por período e categoria
- Tabela e exportação das transações filtradas
- Categorias sugeridas a partir da descrição

## Tecnologias

Python, Streamlit, Pandas e Plotly.

## Privacidade

O app não tem login nem banco remoto. Os dados carregados são processados na sessão do Streamlit; ao hospedar na nuvem, o processamento ocorre na infraestrutura do Streamlit Community Cloud. Não envie extratos com dados sensíveis para uma demonstração pública. Para uma versão pública, prefira arquivos de exemplo anonimizados.

