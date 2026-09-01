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

    def _buscar_trending_de_uma_instancia(
        self, instancia_url: str, limite: int
    ) -> list:
        """
        Consulta o trending_statuses de uma única instância
        não usa access_token pq o endpoint é público na maioria dos casos
        retorna lista vazia se a instância falhar
        """
        try:
            client = Mastodon(
                api_base_url=instancia_url,
                request_timeout=15,
                version_check_mode="none",
            )
            return client.trending_statuses(limit=limite, lang=config.IDIOMA_ALVO)
        except Exception as erro:  # noqa: BLE001
            print(f"[mastodon] falha ao consultar {instancia_url}: {erro}")
            return []

    def coletar(self, limite_por_instancia: int = 25) -> list[Post]:
        """
        Percorre todas as instâncias configuradas, busca os posts em alta
        de cada uma, filtra por idioma e por conta bot, e retorna a lista
        combinada de `Post`
        """
        posts_coletados: list[Post] = []
        uris_ja_vistas: set[str] = set()

        for instancia_url in config.MASTODON_INSTANCES:
            statuses = self._buscar_trending_de_uma_instancia(
                instancia_url, limite_por_instancia
            )

            for status in statuses:
                try:
                    if getattr(status, "uri", None) in uris_ja_vistas:
                        continue  # mesmo post já veio de outra instância

                    if getattr(status, "language", None) != config.IDIOMA_ALVO:
                        continue

                    if getattr(status.account, "bot", False):
                        continue

                    texto_bruto = _limpar_html(status.content)

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
                    uris_ja_vistas.add(status.uri)

                except Exception as erro:  # noqa: BLE001 — mesma decisão do collector do Bluesky
                    identificador = getattr(status, "uri", "desconhecido")
                    print(f"[mastodon] erro ao processar post {identificador}: {erro}")
                    continue

        return posts_coletados
