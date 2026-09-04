import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

import config
from models.post import Post


@contextmanager
def _conectar() -> Iterator[sqlite3.Connection]:
    # Abre uma conexão com o banco e garante que ela seja fechada (com
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = (
        sqlite3.Row
    )  # permite acessar colunas pelo nome, ex: linha["curtidas"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def salvar_candidato(post: Post) -> None:
    """

    Se já existir um post com a mesma plataforma e post_id_origem,
    atualiza as métricas com os valores mais recentes

    Requer que post.engajamento_bruto e post.engajamento_relativo já
    tenham sido calculados via ranking.engagement.aplicar_ranking
    """
    if post.engajamento_bruto is None or post.engajamento_relativo is None:
        raise ValueError(
            "Post precisa passar por ranking.engagement.aplicar_ranking() "
            "antes de ser salvo."
        )

    with _conectar() as conn:
        conn.execute(
            """
            INSERT INTO postagens_candidatas (
                post_id_origem, plataforma, texto_bruto, texto_anonimizado,
                curtidas, compartilhamentos, respostas, seguidores_autor,
                engajamento_bruto, engajamento_relativo,
                flag_sensivel_plataforma, publicado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (plataforma, post_id_origem) DO UPDATE SET
                curtidas = excluded.curtidas,
                compartilhamentos = excluded.compartilhamentos,
                respostas = excluded.respostas,
                seguidores_autor = excluded.seguidores_autor,
                engajamento_bruto = excluded.engajamento_bruto,
                engajamento_relativo = excluded.engajamento_relativo,
                flag_sensivel_plataforma = excluded.flag_sensivel_plataforma,
                atualizado_em = datetime('now')
            """,
            (
                post.post_id_origem,
                post.plataforma,
                post.texto_bruto,
                post.texto_anonimizado,
                post.curtidas,
                post.compartilhamentos,
                post.respostas,
                post.seguidores_autor,
                post.engajamento_bruto,
                post.engajamento_relativo,
                post.flag_sensivel_plataforma,
                post.publicado_em.isoformat(),
            ),
        )


def salvar_varios(posts: list[Post]) -> int:
    for post in posts:
        salvar_candidato(post)
    return len(posts)


def listar_candidatos_para_revisao(limite: int = 50) -> list[sqlite3.Row]:
    # Lista candidatos ainda não revisados manualmente, ordenados do maior
    with _conectar() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM postagens_candidatas
            WHERE revisado_manualmente = 0
            ORDER BY engajamento_relativo DESC
            LIMIT ?
            """,
            (limite,),
        )
        return cursor.fetchall()


def marcar_revisado(candidato_id: int, aprovado: bool) -> None:
    # Marca um candidato como revisado, registrando se foi aprovado ou não
    with _conectar() as conn:
        conn.execute(
            """
            UPDATE postagens_candidatas
            SET revisado_manualmente = 1, aprovado = ?
            WHERE id = ?
            """,
            (aprovado, candidato_id),
        )


def migrar_aprovados_para_postagens() -> int:
    """
    Copia para a tabela final postagens, a que o front vai consumir todos
    os candidatos aprovados que ainda não foram migrados.

    retorna quantos registros foram migrados nesta chamada
    """
    with _conectar() as conn:
        candidatos_aprovados = conn.execute(
            """
            SELECT pc.id, pc.texto_anonimizado, pc.plataforma, pc.engajamento_bruto
            FROM postagens_candidatas pc
            WHERE pc.aprovado = 1
              AND NOT EXISTS (
                  SELECT 1 FROM postagens p WHERE p.candidata_id = pc.id
              )
            """
        ).fetchall()

        for candidato in candidatos_aprovados:
            conn.execute(
                """
                INSERT INTO postagens (texto, origem, engajamento, artificial, candidata_id)
                VALUES (?, ?, ?, 0, ?)
                """,
                (
                    candidato["texto_anonimizado"],
                    candidato["plataforma"],
                    candidato["engajamento_bruto"],
                    candidato["id"],
                ),
            )

        return len(candidatos_aprovados)
