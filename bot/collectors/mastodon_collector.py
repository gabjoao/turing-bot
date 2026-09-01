"""
Collector do Mastodon

O conteúdo de um post no Mastodon vem em HTML, por isso este módulo
tem uma etapa própria de limpeza de HTML antes da anonimização.
"""

import html
import re

from mastodon import Mastodon

import config
from models.post import Post

# Remove qualquer tag HTML (<p>, <a href="...">, <br>, etc.), mantendo só o texto
PADRAO_TAG_HTML = re.compile(r"<[^>]+>")

# REGEX para menções
PADRAO_MENCAO = re.compile(r"@[\w.\-]+(?:@[\w.\-]+)?")


def _limpar_html(conteudo_html: str) -> str:
    # Remove tags HTML e decodifica entidades ex: '&amp;' -> '&'
    texto = re.sub(r"<br\s*/?>", "\n", conteudo_html, flags=re.IGNORECASE)
    texto = re.sub(r"</p>", "\n\n", texto, flags=re.IGNORECASE)
    texto = PADRAO_TAG_HTML.sub("", texto)  # remove tags restantes sem adicionar espaço
    texto = html.unescape(texto)
    texto = re.sub(r"[ \t]+", " ", texto)  # colapsa espaços horizontais repetidos
    texto = re.sub(r"\n{3,}", "\n\n", texto)  # no máximo uma linha em branco
    return texto.strip()


def _anonimizar_mencoes(texto: str) -> str:
    # Substitui qualquer @usuario (local ou federado) por 'Usuário'.
    return PADRAO_MENCAO.sub("Usuário", texto)


def _tem_conteudo_sensivel(status) -> bool:
    # Considera sensível se a própria instância/autor marcou o post como sensível
    marcado_sensivel = getattr(status, "sensitive", False)
    tem_aviso = bool(getattr(status, "spoiler_text", "") or "")
    return marcado_sensivel or tem_aviso


class MastodonCollector:
    """
    Encapsula a conexão com o Mastodon e a coleta de posts em alta

    Uso básico:
        collector = MastodonCollector()
        posts = collector.coletar()
    """

    def __init__(self) -> None:
        self._client = Mastodon(
            access_token=config.MASTODON_ACCESS_TOKEN,
            api_base_url=config.MASTODON_INSTANCE_URL,
        )

    def coletar(self, limite: int = 25) -> list[Post]:
        statuses = self._client.trending_statuses(limit=limite, lang=config.IDIOMA_ALVO)

        posts_coletados: list[Post] = []

        for status in statuses:
            try:
                # trending_statuses() só prioriza o idioma pedido na
                # ordenação e não garante que só venham posts nesse
                # idioma. é filtrado manualmente aqui
                if getattr(status, "language", None) != config.IDIOMA_ALVO:
                    continue

                texto_bruto = _limpar_html(status.content)

                # compartilhamentos inclui reblogs + citações (quotes_count)
                compartilhamentos = (status.reblogs_count or 0) + (
                    getattr(status, "quotes_count", 0) or 0
                )

                post = Post(
                    post_id_origem=status.uri,
                    plataforma="mastodon",
                    texto_bruto=texto_bruto,
                    texto_anonimizado=_anonimizar_mencoes(texto_bruto),
                    curtidas=status.favourites_count or 0,
                    compartilhamentos=compartilhamentos,
                    respostas=status.replies_count or 0,
                    seguidores_autor=status.account.followers_count or 0,
                    publicado_em=status.created_at,
                    flag_sensivel_plataforma=_tem_conteudo_sensivel(status),
                )
                posts_coletados.append(post)

            except Exception as erro:  # noqa: BLE001
                identificador = getattr(status, "uri", "desconhecido")
                print(f"[mastodon] erro ao processar post {identificador}: {erro}")
                continue

        return posts_coletados
