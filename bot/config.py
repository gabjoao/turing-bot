"""
Configuração central do bot.

Carrega variáveis do .env e expõe como constantes prontas para uso.
Nenhum outro módulo deve ler os.environ diretamente, sempre importar daqui.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto bot/ (onde este arquivo está)
BASE_DIR = Path(__file__).resolve().parent

# Carrega o .env que fica ao lado deste arquivo (bot/.env)
load_dotenv(BASE_DIR / ".env")


def _obrigatoria(nome: str) -> str:
    """Lê uma variável de ambiente obrigatória; falha cedo e com mensagem clara se faltar."""
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente '{nome}' não definida. "
            f"Verifique se o arquivo bot/.env existe e está preenchido "
            f"(veja bot/.env.example como referência)."
        )
    return valor


# Credenciais do Bluesky
#
BLUESKY_HANDLE = _obrigatoria("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD = _obrigatoria("BLUESKY_APP_PASSWORD")

# Credenciais do Mastodon

MASTODON_INSTANCE_URL = _obrigatoria("MASTODON_INSTANCE_URL")
MASTODON_ACCESS_TOKEN = _obrigatoria("MASTODON_ACCESS_TOKEN")

# Lista de instâncias consultadas na coleta
# formato no .env: URLs separadas por vírgula.
# Se MASTODON_INSTANCES não for definida, cai de volta para usar só a
# instância principal (MASTODON_INSTANCE_URL)

_INSTANCIAS_RAW = os.getenv("MASTODON_INSTANCES", "")
MASTODON_INSTANCES = [
    instancia.strip() for instancia in _INSTANCIAS_RAW.split(",") if instancia.strip()
] or [MASTODON_INSTANCE_URL]


# Banco de dados
# DB_PATH no .env é relativo à raiz do projeto (turing-bot/), não à pasta bot/.
_DB_PATH_RAW = os.getenv("DB_PATH", "../bd/database.db")
DB_PATH = (BASE_DIR / _DB_PATH_RAW).resolve()

# Caminho do schema.sql, usado pelo storage/init_db.py
SCHEMA_PATH = (BASE_DIR / "../bd/schema.sql").resolve()

# Regras de negócio (métricas de engajamento, filtros)
# Piso mínimo de seguidores usado no denominador do engajamento relativo,
# evita que contas pequenas gerem taxas explosivas por ruído estatístico.
PISO_SEGUIDORES = 80

# Engajamento bruto mínimo para um post ser considerado candidato
# (evita que 1 curtida em conta de 2 seguidores vença só pela matemática).
ENGAJAMENTO_BRUTO_MINIMO = 5

# Idioma alvo do filtro de coleta
IDIOMA_ALVO = "pt"
