-- ============================================================
-- ETL-B3-Pipeline — Schema do Supabase
-- Execute no SQL Editor do Supabase (em ordem)
-- ============================================================


-- ------------------------------------------------------------
-- 1. Tabela principal: cotações históricas
-- ------------------------------------------------------------
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


-- ------------------------------------------------------------
-- 2. Índice único para idempotência + índices de performance
--    UNIQUE INDEX suporta expressões (DATE_TRUNC), diferente de CONSTRAINT UNIQUE.
--    Impede duplicatas na mesma hora para o mesmo ativo.
-- ------------------------------------------------------------
CREATE UNIQUE INDEX uq_symbol_hora      ON cotacoes (symbol, DATE_TRUNC('hour', collected_at));
CREATE INDEX idx_cotacoes_symbol        ON cotacoes (symbol);
CREATE INDEX idx_cotacoes_collected_at  ON cotacoes (collected_at DESC);
CREATE INDEX idx_cotacoes_symbol_data   ON cotacoes (symbol, collected_at DESC);


-- ------------------------------------------------------------
-- 3. View auxiliar: última cotação de cada ativo
--    Usada pelo Worker no endpoint GET /cotacoes
-- ------------------------------------------------------------
CREATE VIEW ultima_cotacao AS
SELECT DISTINCT ON (symbol)
    symbol,
    price,
    change,
    change_pct,
    volume,
    market_cap,
    collected_at
FROM cotacoes
ORDER BY symbol, collected_at DESC;


-- ------------------------------------------------------------
-- 4. Row Level Security (RLS)
--    A anon key do Supabase ficará no Cloudflare Worker (semi-pública).
--    RLS garante que ela só pode fazer SELECT — nunca INSERT/UPDATE/DELETE.
-- ------------------------------------------------------------
ALTER TABLE cotacoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "leitura_publica"
    ON cotacoes
    FOR SELECT
    USING (true);


-- ------------------------------------------------------------
-- 5. Verificação final
--    Rode estas queries para confirmar que tudo foi criado:
-- ------------------------------------------------------------
-- SELECT * FROM cotacoes LIMIT 5;
-- SELECT * FROM ultima_cotacao;
-- SELECT schemaname, tablename, rowsecurity FROM pg_tables WHERE tablename = 'cotacoes';
