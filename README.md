# 📈 Monitor B3 — ETL Pipeline de Dados Financeiros

![ETL Pipeline](https://github.com/vitoralcantarac/ETL-B3-Pipeline/actions/workflows/etl_pipeline.yml/badge.svg)
![Tests](https://github.com/vitoralcantarac/ETL-B3-Pipeline/actions/workflows/tests.yml/badge.svg)
![Deploy Dashboard](https://github.com/vitoralcantarac/ETL-B3-Pipeline/actions/workflows/pages.yml/badge.svg)

Pipeline ETL automatizada que coleta cotações de **ações e FIIs da B3** 3x por dia, armazena no Supabase (PostgreSQL) e exibe em um dashboard interativo publicado no GitHub Pages.

🔗 **[Dashboard ao vivo](https://vitoralcantarac.github.io/ETL-B3-Pipeline)**

---

## 🗺️ Arquitetura

```
[brapi.dev API]
      │
      ▼
[Python ETL]  ◄── GitHub Actions cron (11h / 15h / 18h BRT, dias úteis)
      │
      ├── extract.py   → coleta da API (1 request por ativo, rate-limit seguro)
      ├── transform.py → limpeza, tipagem, validação e timestamp truncado na hora
      └── load.py      → upsert idempotente no Supabase
              │
              ▼
     [Supabase — PostgreSQL]
       · tabela cotacoes   (histórico completo)
       · view ultima_cotacao (preço mais recente por ativo)
       · RLS ativo          (anon key só pode ler)
              │
              ▼
    [Cloudflare Worker]  ◄── API intermediária com whitelist de tickers
       · GET /cotacoes
       · GET /historico?symbol=PETR4&dias=30
              │
              ▼
    [Dashboard — GitHub Pages]
       · Cards por categoria (Ações / FIIs)
       · Gráfico histórico com filtro de período
       · Tabela completa com volume e market cap
       · Auto-refresh a cada 5 minutos
```

---

## 🛠️ Stack

| Camada | Tecnologia | Função |
|---|---|---|
| Dados | [brapi.dev](https://brapi.dev) | API gratuita com cotações da B3 em tempo real |
| ETL | Python 3.11 — pandas, requests, supabase-py | Extração, transformação e carga |
| Banco | [Supabase](https://supabase.com) (PostgreSQL) | Armazenamento histórico com RLS |
| Orquestração | GitHub Actions (cron) | Agendamento automático sem servidor próprio |
| API | [Cloudflare Workers](https://workers.cloudflare.com) | Proxy seguro entre banco e dashboard |
| Frontend | HTML + CSS + JS ([Chart.js](https://chartjs.org)) | Dashboard estático sem framework |
| Hospedagem | GitHub Pages | Deploy automático a cada push |

---

## 📦 Ativos Monitorados

**Ações:** `PETR4` · `VALE3` · `ITUB4` · `BBDC4` · `MGLU3`

**FIIs:** `MXRF11` · `HGLG11` · `KNRI11`

---

## ⚙️ Como rodar localmente

**Pré-requisitos:** Python 3.11+, conta no [brapi.dev](https://brapi.dev) e projeto no [Supabase](https://supabase.com)

```bash
# 1. Clone o repositório
git clone https://github.com/vitoralcantarac/ETL-B3-Pipeline.git
cd ETL-B3-Pipeline

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 4. Execute o schema no Supabase
# Copie o conteúdo de sql/schema.sql e execute no SQL Editor do Supabase

# 5. Rode a pipeline
python -m etl.pipeline

# 6. Rode os testes
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 🗄️ Schema do Banco

```sql
-- Histórico de cotações com controle de duplicatas por hora
CREATE TABLE cotacoes (
    id           BIGSERIAL PRIMARY KEY,
    symbol       TEXT          NOT NULL,
    price        NUMERIC(12,2),
    change       NUMERIC(12,2),
    change_pct   NUMERIC(8,4),
    volume       BIGINT,
    market_cap   BIGINT,
    collected_at TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- Índice único: impede duplicatas na mesma hora para o mesmo ativo
CREATE UNIQUE INDEX uq_symbol_hora ON cotacoes (symbol, DATE_TRUNC('hour', collected_at));

-- View: última cotação de cada ativo (usada pelo endpoint /cotacoes)
CREATE VIEW ultima_cotacao AS
SELECT DISTINCT ON (symbol) * FROM cotacoes ORDER BY symbol, collected_at DESC;
```

---

## 🔐 Segurança

- **`.env` no `.gitignore`** — credenciais nunca chegam ao repositório
- **RLS no Supabase** — a `anon key` (exposta no Worker) só pode fazer `SELECT`
- **`service_role key`** — usada apenas no ETL via GitHub Actions Secrets (criptografados)
- **Whitelist no Worker** — endpoint `/historico` valida o parâmetro `symbol` contra lista fixa

---

## 🧠 Decisões Técnicas

**Por que truncar `collected_at` na hora?**
O timestamp é sempre gravado como `HH:00:00`, tornando o índice `UNIQUE (symbol, collected_at)` equivalente a um unique-por-hora. Isso garante idempotência: se o job rodar duas vezes no mesmo período, o segundo upsert é ignorado silenciosamente.

**Por que Cloudflare Worker em vez de expor o Supabase diretamente?**
A `anon key` do Supabase precisaria ficar no JavaScript do browser — qualquer pessoa poderia usá-la para acessar o banco diretamente. O Worker atua como proxy: recebe as requisições do dashboard, valida os parâmetros e faz a query ao Supabase com a chave nunca exposta ao browser.

**Por que `df.where(df.notna(), other=None)` no transform?**
Colunas `Int64` nullable do pandas geram `pd.NA` ao invés de `None`. O cliente supabase-py serializa isso para JSON como `NaN`, que não é válido. O `.where()` converte todos os `pd.NA` para `None` antes da serialização.

**Por que GitHub Actions em vez de um servidor?**
Zero custo de infraestrutura, log de execuções visível no repositório público (demonstra a pipeline rodando de verdade) e configuração declarativa em YAML versionada junto ao código.

---

## 📁 Estrutura do Projeto

```
ETL-B3-Pipeline/
├── .github/
│   └── workflows/
│       ├── etl_pipeline.yml   # Cron 3x/dia + trigger manual
│       └── pages.yml          # Deploy automático do dashboard
├── etl/
│   ├── extract.py             # Coleta da brapi.dev
│   ├── transform.py           # Limpeza, validação e tipagem
│   ├── load.py                # Upsert idempotente no Supabase
│   └── pipeline.py            # Orquestrador com logging e error handling
├── tests/
│   └── test_transform.py      # 11 testes unitários do transform
├── worker/
│   ├── index.js               # Cloudflare Worker (2 endpoints)
│   └── wrangler.toml          # Configuração do Worker
├── dashboard/
│   ├── index.html
│   ├── style.css              # Tema escuro financeiro
│   └── app.js                 # Fetch, renderização e auto-refresh
├── sql/
│   └── schema.sql             # Tabela, índices, view, RLS e GRANT
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

---

## 🚀 Deploy

| Componente | Onde | Como |
|---|---|---|
| ETL | GitHub Actions | Automático via cron |
| Banco | Supabase | Schema em `sql/schema.sql` |
| API | Cloudflare Workers | `wrangler deploy` na pasta `worker/` |
| Dashboard | GitHub Pages | Automático a cada push em `main` |

---

## 🎓 Aprendizados

**O que aprendi construindo esse projeto:**

- **RLS no Supabase tem nuances**: views precisam de `GRANT SELECT` explícito para a role `anon` — não herdam automaticamente as políticas da tabela base.
- **Tipos nullable do pandas não serializam para JSON**: colunas `Int64` geram `pd.NA` em vez de `None`. Solução: `df.where(df.notna(), other=None)` antes do upsert.
- **Idempotência requer design intencional**: sem timestamp truncado na hora + índice `UNIQUE`, cada re-execução geraria duplicatas silenciosas no banco.
- **`UNIQUE` com expressão não funciona em `CONSTRAINT` inline**: `CONSTRAINT uq UNIQUE (symbol, DATE_TRUNC(...))` é inválido no PostgreSQL — precisa ser `CREATE UNIQUE INDEX`.
- **Secrets com newline quebram conexões HTTP silenciosamente**: copiar e colar de alguns editores adiciona `\n` no final, causando `InvalidURL` profundo na stack do httpx.
- **Cloudflare Workers em modo não-interativo**: o terminal integrado do VS Code não exibe prompts do Wrangler — a solução foi passar o valor via pipe no PowerShell.
- **`anon key` vs `service_role key`**: a `anon key` é restrita pelo RLS (leitura pública), a `service_role` bypassa tudo — cada uma tem seu lugar certo na arquitetura.

**O que faria diferente numa próxima versão:**

- Separaria as variáveis com nomes distintos (`SUPABASE_SERVICE_KEY` e `SUPABASE_ANON_KEY`) para tornar o papel de cada chave explícito no código.
- Adicionaria testes de integração com mock da brapi.dev para cobrir `extract.py` sem depender de conexão real.
- Usaria migrações versionadas (ex: Flyway ou scripts numerados) em vez de um único `schema.sql` para facilitar evoluções do banco.
- Automatizaria o deploy do Cloudflare Worker via GitHub Actions (`wrangler deploy` no CI) em vez de rodar manualmente no terminal — é o único componente do projeto que ainda exige intervenção manual a cada atualização.
