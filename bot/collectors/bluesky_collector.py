"""

A API de busca do Bluesky (search_posts) exige um termo de busca, não dá
para pedir "todos os posts em alta" sem palavra-chave nenhuma. Para não
restringir a coleta a um tema específico, tem uma lista rotativa de
termos bem genéricos
a cada coleta, um termo é sorteado, e a busca
é ordenada por engajamento e filtrada por idioma na própria

Este módulo NÃO decide o que é aprovado ou não, só traduz a resposta da
API para o modelo unificado `Post`. Cálculo de engajamento fica a cargo
de ranking/engagement.py; decisão de aprovação fica para a revisão manual.
"""

import random
import re
from datetime import datetime

from atproto import Client

import config
from models.post import Post


# Termos genéricos para iniciar a busca
TERMOS_SEED = [
    "que",
    "q",
    "para",
    "não",
    "hoje",
    "vida",
    "tempo",
    "gente",
    "assim",
    "aqui",
    "agora",
    "sempre",
    "nunca",
    "bom",
    "dia",
    "em",
    "te",
    "eu",
    "de",
    "da",
    "do",
    "o",
    "a",
    "um",
    "uma",
    "se",
    "meu",
    "minha",
    "seu",
    "sua",
    "teu",
    "tua",
    "cara",
    "de",
    "em",
    "é",
    "mas",
    "pq",
    "pqp",
    "meio",
    "como",
    "quem",
    "mano",
    "ta",
    "ne",
    "tudo",
    "todos",
    "todo",
]

# REGEX que reconhece menções,
# "." e "-" para lidar com o formato "usuario.bsky.social" do Bluesky
PADRAO_MENCAO = re.compile(r"@[\w.\-]+")


def _anonimizar_mencoes(texto: str) -> str:
    return PADRAO_MENCAO.sub("@Usuário", texto)


def _tem_label_sensivel(post_view) -> bool:
    # Verifica se o post tem alguma label de conteúdo sensível
    labels = getattr(post_view, "labels", None) or []
    return len(labels) > 0


class BlueskyCollector:
    """
    Encapsula a conexão com o Bluesky e a coleta de posts.

    Uso básico:
        collector = BlueskyCollector()
        posts = collector.coletar()
    """

    def __init__(self) -> None:
        self._client = Client()
        self._autenticado = False

    def autenticar(self) -> None:
        # Faz login
        self._client.login(config.BLUESKY_HANDLE, config.BLUESKY_APP_PASSWORD)
        self._autenticado = True

    def _buscar_seguidores(self, did: str) -> int:
        # Busca o número de seguidores do autor de um post.

        perfil = self._client.app.bsky.actor.get_profile({"actor": did})
        return getattr(perfil, "followers_count", 0) or 0

    def coletar(self, limite_por_termo: int = 25) -> list[Post]:

        # sorteia um termo seed, busca posts ordenados por engajamento em pt-BR, e retorna uma lista de `Post`
        # já no formato unificado.
        if not self._autenticado:
            self.autenticar()

        termo = random.choice(TERMOS_SEED)

        resposta = self._client.app.bsky.feed.search_posts(
            {
                "q": termo,
                "sort": "top",
                "lang": config.IDIOMA_ALVO,
                "limit": limite_por_termo,
            }
        )

        posts_coletados: list[Post] = []

        for post_view in resposta.posts:
            try:
                raw_texto = getattr(post_view.record, "text", None)
                raw_criado_em = getattr(post_view.record, "created_at", None)

                if raw_texto is None or raw_criado_em is None:
                    raise ValueError(
                        f"registro sem texto ou data de criação: {post_view.uri}"
                    )

                texto_bruto = raw_texto
                publicado_em = datetime.fromisoformat(raw_criado_em)
                seguidores = self._buscar_seguidores(post_view.author.did)
                compartilhamentos = (post_view.repost_count or 0) + (
                    post_view.quote_count or 0
                )

                post = Post(
                    post_id_origem=post_view.uri,
                    plataforma="bluesky",
                    texto_bruto=texto_bruto,
                    texto_anonimizado=_anonimizar_mencoes(texto_bruto),
                    curtidas=post_view.like_count or 0,
                    compartilhamentos=compartilhamentos,
                    respostas=post_view.reply_count or 0,
                    seguidores_autor=seguidores,
                    publicado_em=publicado_em,
                    flag_sensivel_plataforma=_tem_label_sensivel(post_view),
                )
                posts_coletados.append(post)

            except Exception as erro:  # noqa: BLE001
                identificador = getattr(post_view, "uri", "desconhecido")
                print(f"[bluesky] erro ao processar post {identificador}: {erro}")
                continue

        return posts_coletados
