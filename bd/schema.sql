-- =====================================================================
-- Schema: coleta e curadoria de postagens (TCC)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Tabela de staging: tudo que o bot coleta passa por aqui primeiro.
-- Só o pesquisador e o pipeline de coleta usam esta tabela.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS postagens_candidatas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificação de origem (essencial para dedup / upsert)
    post_id_origem          TEXT    NOT NULL,
    plataforma              TEXT    NOT NULL CHECK (plataforma IN ('bluesky', 'mastodon')),

    -- Conteúdo
    texto_bruto             TEXT    NOT NULL,   -- texto original, uso interno apenas
    texto_anonimizado       TEXT    NOT NULL,   -- menções @usuario já substituídas

    -- Métricas de engajamento (capturadas no momento da coleta/atualização)
    curtidas                INTEGER NOT NULL DEFAULT 0,
    compartilhamentos       INTEGER NOT NULL DEFAULT 0,   -- reposts / reblogs
    respostas               INTEGER NOT NULL DEFAULT 0,
    seguidores_autor        INTEGER NOT NULL DEFAULT 0,

    -- Métricas derivadas (calculadas pela camada de ranking, não pela API)
    engajamento_bruto       INTEGER NOT NULL DEFAULT 0,   -- curtidas + compartilhamentos + respostas
    engajamento_relativo    REAL,                          -- engajamento_bruto / max(seguidores_autor, 80)

    -- Moderação / triagem
    flag_sensivel_plataforma BOOLEAN NOT NULL DEFAULT 0,   -- veio do sensitive/labels nativo da API
    revisado_manualmente    BOOLEAN NOT NULL DEFAULT 0,
    aprovado                BOOLEAN,                        -- NULL = ainda não decidido

    -- Datas
    publicado_em            DATETIME NOT NULL,             -- data original do post na rede
    coletado_em              DATETIME NOT NULL DEFAULT (datetime('now')),
    atualizado_em            DATETIME NOT NULL DEFAULT (datetime('now')),

    -- Um mesmo post não pode ser duplicado dentro da mesma plataforma
    UNIQUE (plataforma, post_id_origem)
);

-- Índices de apoio às queries mais comuns
CREATE INDEX IF NOT EXISTS idx_candidatas_ranking
    ON postagens_candidatas (aprovado, engajamento_relativo DESC);

CREATE INDEX IF NOT EXISTS idx_candidatas_plataforma
    ON postagens_candidatas (plataforma);

CREATE INDEX IF NOT EXISTS idx_candidatas_revisao
    ON postagens_candidatas (revisado_manualmente, aprovado);


-- ---------------------------------------------------------------------
-- Tabela final: a que o front / teste com participantes consome.
-- Só recebe registros migrados manualmente da staging (aprovado = 1)
-- e os posts artificiais gerados pelo modelo de IA.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS postagens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    texto         TEXT    NOT NULL,
    origem        TEXT    NOT NULL CHECK (origem IN ('bluesky', 'mastodon', 'modelo_ia')),

    -- soma bruta de curtidas + compartilhamentos + respostas;
    -- NULL para linhas artificiais (origem = 'modelo_ia'), pois não têm engajamento real
    engajamento   INTEGER,

    artificial    BOOLEAN NOT NULL DEFAULT 0,

    -- referência de rastreabilidade: liga de volta ao registro de staging
    -- (NULL quando origem = 'modelo_ia')
    candidata_id  INTEGER REFERENCES postagens_candidatas(id),

    criado_em     DATETIME NOT NULL DEFAULT (datetime('now')),

    -- Regra de consistência: post artificial não deve ter engajamento nem candidata_id
    CHECK (
        (artificial = 1 AND engajamento IS NULL AND candidata_id IS NULL)
        OR
        (artificial = 0 AND candidata_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_postagens_origem
    ON postagens (origem);
