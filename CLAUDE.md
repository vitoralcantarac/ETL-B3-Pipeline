# ETL Pipeline Financeiro — Monitor B3

Pipeline ETL automatizada que coleta cotações de ações e FIIs brasileiros via brapi.dev, armazena no Supabase (PostgreSQL) e exibe num dashboard interativo publicado no GitHub Pages.

## Objetivo

Projeto de portfólio para demonstrar habilidades de engenharia de dados: Python, SQL, cloud, automação e visualização. Dados atualizados 3x por dia (dias úteis) via GitHub Actions.

---

## Arquitetura

```
[brapi.dev API]
      │
      ▼
[Python ETL]  ←── GitHub Actions cron (3x/dia, dias úteis)
      │
      ├── etl/extract.py     → coleta dados da API
      ├── etl/transform.py   → limpeza, tipagem, validação
      └── etl/load.py        → upsert no Supabase (idempotente)
              │
              ▼
       [Supabase — PostgreSQL]
              │
              ▼
    [Cloudflare Worker]  ←── API intermediária (protege credenciais, resolve CORS)
              │
              ▼
    [Dashboard HTML/JS]  ←── GitHub Pages (Chart.js, vanilla JS)
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Dados | brapi.dev (API gratuita, B3 em tempo real) |
| ETL | Python 3.11 — pandas, requests, supabase-py |
| Banco | Supabase (PostgreSQL) |
| Orquestração | GitHub Actions (cron) |
| API intermediária | Cloudflare Worker |
| Frontend | HTML + CSS + JS (Chart.js via CDN) |
| Hospedagem | GitHub Pages |

---

## Estrutura de Pastas

```
etl-financeiro-b3/
├── .github/
│   └── workflows/
│       └── etl_pipeline.yml       # Agendamento automático
│
├── etl/
│   ├── __init__.py
│   ├── extract.py                 # Coleta da brapi.dev
│   ├── transform.py               # Limpeza e validação com pandas
│   ├── load.py                    # Upsert idempotente no Supabase
│   └── pipeline.py                # Orquestra extract → transform → load
│
├── tests/
│   ├── __init__.py
│   └── test_transform.py          # Testes unitários do transform
│
├── worker/
│   └── index.js                   # Cloudflare Worker (API REST)
│
├── dashboard/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── sql/
│   └── schema.sql                 # Schema + RLS + índices + view
│
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Ativos Monitorados

**Ações:**
- `PETR4` — Petrobras
- `VALE3` — Vale
- `ITUB4` — Itaú Unibanco
- `BBDC4` — Bradesco
- `MGLU3` — Magazine Luiza

**FIIs:**
- `MXRF11` — Maxi Renda
- `HGLG11` — CSHG Logística
- `KNRI11` — Kinea Renda Imobiliária

---

## Variáveis de Ambiente

Copiar `.env.example` para `.env` (nunca commitar `.env`):

```
BRAPI_TOKEN=seu_token_aqui
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
```

No GitHub Actions, configurar como Secrets em:
`Settings → Secrets and variables → Actions`

No Cloudflare Worker, configurar com:
```bash
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
```

---

## Comandos de Desenvolvimento

```bash
# Instalar dependências de produção
pip install -r requirements.txt

# Instalar dependências de desenvolvimento (inclui pytest)
pip install -r requirements-dev.txt

# Rodar a pipeline localmente (requer .env preenchido)
python -m etl.pipeline

# Rodar os testes
pytest tests/

# Rodar um step isolado (para debug)
python -c "from etl.extract import extract; print(extract())"
```

---

## Schema do Banco (resumo)

Tabela principal: `cotacoes`
- `symbol`, `price`, `change`, `change_pct`, `volume`, `market_cap`, `collected_at`
- Constraint `UNIQUE (symbol, DATE_TRUNC('hour', collected_at))` — garante idempotência
- RLS habilitada: somente leitura para a `anon key`

View auxiliar: `ultima_cotacao`
- Retorna a cotação mais recente de cada ativo (usada pelo Worker no endpoint `/cotacoes`)

---

## Decisões Técnicas

- **Imports absolutos** (`from etl.extract import extract`): necessário para o GitHub Actions executar `python -m etl.pipeline` a partir da raiz.
- **Upsert com ON CONFLICT**: evita duplicatas quando o job é re-executado manualmente.
- **`df.where(df.notna(), None)`** no transform: converte `pd.NA` (Int64 nullable) para `None` antes da serialização JSON para o Supabase.
- **Cloudflare Worker como proxy**: protege as credenciais do Supabase e resolve CORS para o dashboard.
- **RLS no Supabase**: a `anon key` está semi-exposta no Worker; RLS garante somente leitura.
- **`logging` em vez de `print`**: saída estruturada visível nos logs do GitHub Actions.

---

## Dashboard

Tema escuro financeiro. Componentes:

1. **Cards por ativo** — preço atual + variação % com cor verde/vermelho
2. **Gráfico de linha** — histórico com seletor de ativo e filtro de período (7/30/90 dias)
3. **Tabela completa** — todos os ativos com volume e market cap formatados
4. **Auto-refresh** — atualiza a cada 5 minutos com countdown visível
5. **Timestamp** — "Última atualização: DD/MM HH:MM"

Paleta:
- Fundo: `#0F172A` | Cards: `#1E293B` | Borda: `#334155`
- Positivo: `#22C55E` | Negativo: `#EF4444`
- Texto: `#F1F5F9` | Secundário: `#94A3B8` | Accent: `#3B82F6`

---

## Segurança

- Nunca commitar `.env` (está no `.gitignore`)
- Nunca usar a `service_role` key no Worker — usar apenas a `anon key`
- RLS configurada na tabela `cotacoes` (somente SELECT público)
- Worker valida o parâmetro `symbol` contra whitelist antes de consultar o Supabase
