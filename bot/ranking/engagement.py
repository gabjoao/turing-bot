"""
Cálculio das métricas derivadas de engajamento

esse módulo NÃO decide se um post é salvo ou aprovado, ele só calcula os
números que os outros módulos (storage, revisão manual) vão usar para
decidir. A fórmula é a mesma para as duas plataformas, então fica
centralizada aqui em vez de duplicada dentro de cada collector
"""

import config
from models.post import Post


def calcular_engajamento_bruto(post: Post) -> int:
    # Soma simples das três métricas de interação
    return post.curtidas + post.compartilhamentos + post.respostas


def calcular_engajamento_relativo(
    engajamento_bruto: int, seguidores_autor: int
) -> float:
    """
    Normaliza o engajamento bruto pelo tamanho da audiência do autor

    Usa um piso mínimo de seguidores (config.PISO_SEGUIDORES) no
    denominador, para evitar que contas pequenas gerem taxas explosivas
    por ruído estatístico    ex: conta com 2 seguidores e 1 curtida daria
    uma taxa de 0.5 (50%), parecendo "viral" sem ser de fato relevante
    """
    denominador = max(seguidores_autor, config.PISO_SEGUIDORES)
    return engajamento_bruto / denominador


def aplicar_ranking(post: Post) -> Post:
    post.engajamento_bruto = calcular_engajamento_bruto(post)
    post.engajamento_relativo = calcular_engajamento_relativo(
        post.engajamento_bruto, post.seguidores_autor
    )
    return post


def atende_minimo(post: Post) -> bool:
    """
    Verifica se o post atinge o piso mínimo de engajamento bruto absoluto
    (config.ENGAJAMENTO_BRUTO_MINIMO) — filtro complementar ao engajamento
    relativo, para barrar casos como 1 curtida numa conta de 2 seguidores,
    que venceriam só pela matemática da taxa relativa.

    """
    if post.engajamento_bruto is None:
        raise ValueError(
            "post.engajamento_bruto ainda não foi calculado — "
            "chame aplicar_ranking(post) antes de atende_minimo(post)."
        )
    return post.engajamento_bruto >= config.ENGAJAMENTO_BRUTO_MINIMO


def ordenar_por_engajamento(posts: list[Post]) -> list[Post]:
    return sorted(
        posts,
        key=lambda p: p.engajamento_relativo or 0.0,
        reverse=True,
    )
