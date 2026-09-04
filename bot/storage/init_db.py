import sqlite3

import config


def init_db() -> None:
    # Garante que a pasta bd/ existe antes de tentar criar o arquivo do banco
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(config.DB_PATH)
    with open(config.SCHEMA_PATH, encoding="utf-8") as arquivo_schema:
        conn.executescript(arquivo_schema.read())
    conn.commit()
    conn.close()

    print(f"Banco inicializado em: {config.DB_PATH}")


if __name__ == "__main__":
    init_db()
