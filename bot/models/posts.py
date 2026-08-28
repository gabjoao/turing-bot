from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    # identificação de origem usados para deduplicar (UNIQUE no banco)
    post_id_origem: str
    plataforma: str  # "bluesky" ou "mastodon"

    # Conteúdo
    texto_bruto: str
    texto_anonimizado: str

    # Métricas brutas, direto da API
    curtidas: int
    compartilhamentos: int
    respostas: int
    seguidores_autor: int

    # Data original de publicação do post na rede
    publicado_em: datetime

    # Moderação — vem dos flags nativos da API
    flag_sensivel_plataforma: bool = False

    # Métricas derivadas — começam vazias; quem preenche é o módulo
    # ranking/engagement.py, não o collector. Ficam Optional porque
    # um Post recém-criado pelo collector ainda não passou por esse cálculo
    engajamento_bruto: Optional[int] = None
    engajamento_relativo: Optional[float] = None

    def __post_init__(self) -> None:
        # validações iniciais
        #
        plataformas_validas = {"bluesky", "mastodon"}
        if self.plataforma not in plataformas_validas:
            raise ValueError(
                f"plataforma inválida: '{self.plataforma}'. "
                f"Esperado um destes: {plataformas_validas}"
            )
        if self.curtidas < 0 or self.compartilhamentos < 0 or self.respostas < 0:
            raise ValueError("métricas de engajamento não podem ser negativas")
