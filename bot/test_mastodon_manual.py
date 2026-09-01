"""
Script de teste manual para o Mastodon

não faz parte do pipeline do bot
"""

import config
from mastodon import Mastodon
from collectors.mastodon_collector import MastodonCollector


def testar_conexao_crua() -> None:
    # Busca os posts em alta direto, imprimindo o objeto bruto retornado
    # pela API
    print("=== Teste 1: conexão crua com a API ===\n")

    client = Mastodon(
        access_token=config.MASTODON_ACCESS_TOKEN,
        api_base_url=config.MASTODON_INSTANCE_URL,
    )

    statuses = client.trending_statuses(limit=5, lang=config.IDIOMA_ALVO)

    if not statuses:
        print("Nenhum post em alta retornado.")
        return

    primeiro = statuses[0]
    print(f"Quantidade de posts retornados: {len(statuses)}\n")
    print("--- Objeto bruto do primeiro post ---")
    print(primeiro)
    print()

    campos_esperados = [
        "uri",
        "language",
        "content",
        "favourites_count",
        "reblogs_count",
        "replies_count",
        "sensitive",
        "spoiler_text",
        "created_at",
    ]
    for campo in campos_esperados:
        valor = getattr(primeiro, campo, "<<CAMPO NÃO ENCONTRADO>>")
        print(f"{campo}: {valor}")

    print()
    print(
        "quotes_count (pode não existir em todas as instâncias):",
        getattr(primeiro, "quotes_count", "<<CAMPO NÃO ENCONTRADO>>"),
    )
    print(
        "account.followers_count:",
        getattr(primeiro.account, "followers_count", "<<CAMPO NÃO ENCONTRADO>>"),
    )

    print()
    print("--- Idiomas dos posts retornados (para conferir o filtro) ---")
    for s in statuses:
        print(f"  {getattr(s, 'language', '?')}: {getattr(s, 'uri', '?')}")


def testar_coletor_completo() -> None:
    # Testa o MastodonCollector real
    print(
        f"\n=== Teste 2: coletor completo (MastodonCollector, instâncias: {config.MASTODON_INSTANCES}) ===\n"
    )

    collector = MastodonCollector()
    posts = collector.coletar(limite_por_instancia=10)

    print(
        f"Posts coletados e traduzidos com sucesso (após filtro de idioma): {len(posts)}\n"
    )
    for post in posts:
        print(f"- [{post.plataforma}] {post.post_id_origem}")
        print(f"  texto original:     {post.texto_bruto[:200]!r}")
        print(f"  texto anonimizado:  {post.texto_anonimizado[:200]!r}")
        print(
            f"  curtidas={post.curtidas} compartilhamentos={post.compartilhamentos} "
            f"respostas={post.respostas} seguidores={post.seguidores_autor}"
        )
        print(
            f"  publicado_em: {post.publicado_em} (tipo: {type(post.publicado_em).__name__})"
        )
        print(f"  sensivel: {post.flag_sensivel_plataforma}")
        print()


if __name__ == "__main__":
    testar_conexao_crua()
    testar_coletor_completo()
