"""
Script de teste manual.


Não faz parte do pipeline do bot
"""

import config
from atproto import Client
from collectors.bluesky_collector import BlueskyCollector


def testar_conexao_crua() -> None:
    # Faz login e uma busca simples imprimindo o objeto bruto retornado
    print("=== Teste 1: conexão crua com a API ===\n")

    client = Client()
    client.login(config.BLUESKY_HANDLE, config.BLUESKY_APP_PASSWORD)
    print("Login OK.\n")

    resposta = client.app.bsky.feed.search_posts(
        {"q": "hoje", "sort": "top", "lang": "pt", "limit": 3}
    )

    if not resposta.posts:
        print("A busca não retornou nenhum post.")
        return

    primeiro = resposta.posts[0]
    print(f"Quantidade de posts retornados: {len(resposta.posts)}\n")
    print("--- Campos do primeiro post (objeto bruto) ---")
    print(primeiro)
    print()

    # Tenta acessar cada campo individualmente, avisando se algum não existir
    campos_esperados = ["uri", "like_count", "repost_count", "reply_count", "labels"]
    for campo in campos_esperados:
        valor = getattr(primeiro, campo, "<<CAMPO NÃO ENCONTRADO>>")
        print(f"{campo}: {valor}")

    print()
    print("record.text:", getattr(primeiro.record, "text", "<<NÃO ENCONTRADO>>"))
    print(
        "record.created_at:",
        getattr(primeiro.record, "created_at", "<<NÃO ENCONTRADO>>"),
    )
    print("author.did:", getattr(primeiro.author, "did", "<<NÃO ENCONTRADO>>"))


def testar_perfil() -> None:
    # Testa de busca para o número de seguidores de um autor
    print("\n=== Teste 2: busca de perfil (seguidores) ===\n")

    client = Client()
    client.login(config.BLUESKY_HANDLE, config.BLUESKY_APP_PASSWORD)

    # Usa o próprio handle do bot como teste, já que sabemos que ele existe
    perfil = client.app.bsky.actor.get_profile({"actor": config.BLUESKY_HANDLE})
    print("Perfil retornado:", perfil)
    print(
        "followers_count:",
        getattr(perfil, "followers_count", "<<CAMPO NÃO ENCONTRADO>>"),
    )


def testar_coletor_completo() -> None:
    # Testa o BlueskyCollector real

    print("\n=== Teste 3: coletor completo (BlueskyCollector) ===\n")

    collector = BlueskyCollector()
    posts = collector.coletar(limite_por_termo=5)

    print(f"Posts coletados e traduzidos com sucesso: {len(posts)}\n")
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
    testar_perfil()
    testar_coletor_completo()
