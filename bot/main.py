"""

busca posts no Bluesky e no Mastodon,
calcula o engajamento de cada um, descarta os que não atingem o piso
mínimo definido em config.ENGAJAMENTO_BRUTO_MINIMO, e salva os
candidatos restantes na tabela de staging

"""

from collectors.bluesky_collector import BlueskyCollector
from collectors.mastodon_collector import MastodonCollector
from models.post import Post
from ranking.engagement import aplicar_ranking, atende_minimo
from storage import repository
from storage.init_db import init_db


def coletar_bluesky() -> list[Post]:
    """
    Executa a coleta do Bluesky isoladamente
    caso a plataforma falhar inteira, vai registrar o erro e
    devolver lista vazia, não é para impedir a coleta do Mastodon.
    """
    print("--- Coletando do Bluesky ---")
    try:
        posts = BlueskyCollector().coletar()
        print(f"{len(posts)} posts coletados do Bluesky.")
        return posts
    except Exception as erro:  # noqa: BLE001
        print(f"[main] falha ao coletar do Bluesky: {erro}")
        return []


def coletar_mastodon() -> list[Post]:
    # mesma lógica de isolamento de falha mas para o Mastodon
    print("--- Coletando do Mastodon ---")
    try:
        posts = MastodonCollector().coletar()
        print(f"{len(posts)} posts coletados do Mastodon.")
        return posts
    except Exception as erro:  # noqa: BLE001
        print(f"[main] falha ao coletar do Mastodon: {erro}")
        return []


def processar_e_salvar(posts: list[Post]) -> tuple[int, int]:
    """
    Calcula o engajamento de cada post e salva na staging só os que
    atingem o piso mínimo, os demais são descartados

    Retorna quantidade_salva e quantidade_descartada usado só para o
    resumo no final da execução
    """
    salvos = 0
    descartados = 0

    for post in posts:
        aplicar_ranking(post)

        if not atende_minimo(post):
            descartados += 1
            continue

        repository.salvar_candidato(post)
        salvos += 1

    return salvos, descartados


def main() -> None:
    init_db()  # garante que as tabelas existem, mesmo na primeira execução

    posts_bluesky = coletar_bluesky()
    posts_mastodon = coletar_mastodon()
    todos_os_posts = posts_bluesky + posts_mastodon

    print(f"\nTotal coletado nas duas plataformas: {len(todos_os_posts)}")

    salvos, descartados = processar_e_salvar(todos_os_posts)

    print("\n--- Resumo da execução ---")
    print(f"Salvos na staging (novos ou atualizados): {salvos}")
    print(f"Descartados (engajamento abaixo do piso mínimo): {descartados}")


if __name__ == "__main__":
    main()
