"""
Ferramenta de revisão manual dos candidatos coletados

Mostra um candidato por vez, o de maior engajamento relativo primeiro,
pede para aprovar ou rejeitar, e ao final oferece migrar os aprovados
para a tabela final de postagens

"""

from storage import repository


def _formatar_candidato(candidato) -> str:
    # Monta um bloco de texto legível com os dados relevantes para a decisão
    sensivel = "SIM" if candidato["flag_sensivel_plataforma"] else "não"
    return (
        f"\n{'=' * 70}\n"
        f"[{candidato['plataforma']}] id={candidato['id']}\n"
        f"Engajamento: bruto={candidato['engajamento_bruto']} | "
        f"relativo={candidato['engajamento_relativo']:.4f} | "
        f"seguidores={candidato['seguidores_autor']}\n"
        f"Sensível (flag da plataforma): {sensivel}\n"
        f"Publicado em: {candidato['publicado_em']}\n"
        f"{'-' * 70}\n"
        f"{candidato['texto_anonimizado']}\n"
        f"{'=' * 70}"
    )


def _perguntar_decisao() -> str:
    # Pergunta a decisão do usuário até receber uma resposta válida
    while True:
        escolha = (
            input("Aprovar este post? [s]im / [n]ão / [p]ular / [q]sair: ")
            .strip()
            .lower()
        )
        if escolha in ("s", "n", "p", "q"):
            return escolha
        print("Opção inválida — digite s, n, p ou q.")


def revisar() -> None:
    candidatos = repository.listar_candidatos_para_revisao()

    if not candidatos:
        print("Nenhum candidato pendente de revisão no momento.")
        return

    print(f"{len(candidatos)} candidato(s) pendente(s) de revisão.")
    print("Comandos: [s] aprovar  [n] rejeitar  [p] pular por agora  [q] sair\n")

    aprovados = 0
    rejeitados = 0
    pulados = 0

    for candidato in candidatos:
        print(_formatar_candidato(candidato))
        decisao = _perguntar_decisao()

        if decisao == "q":
            print("\nSaindo da revisão. O que já foi decidido está salvo.")
            break
        if decisao == "s":
            repository.marcar_revisado(candidato["id"], aprovado=True)
            aprovados += 1
        elif decisao == "n":
            repository.marcar_revisado(candidato["id"], aprovado=False)
            rejeitados += 1
        elif decisao == "p":
            pulados += 1

    print("\n--- Resumo da revisão ---")
    print(f"Aprovados: {aprovados}")
    print(f"Rejeitados: {rejeitados}")
    print(f"Pulados (continuam pendentes para a próxima vez): {pulados}")

    if aprovados > 0:
        resposta = (
            input(
                f"\nMigrar os {aprovados} aprovado(s) para a tabela final agora? [s/n]: "
            )
            .strip()
            .lower()
        )
        if resposta == "s":
            quantidade = repository.migrar_aprovados_para_postagens()
            print(f"{quantidade} post(s) migrado(s) para a tabela final (postagens).")
        else:
            print("Migração adiada, 'migrar_aprovados_para_postagens()")


if __name__ == "__main__":
    try:
        revisar()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário. O que já foi decidido está salvo.")
