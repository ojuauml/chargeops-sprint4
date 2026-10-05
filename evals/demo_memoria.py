from src import config
from src.chain.builder import ChargeOpsAssistant, criar_llm

TURNOS = [
    "Oi! Eu sou do apto 202.",
    "Quanto eu consumi esse mês?",
    "E quanto eu teria pago se tivesse carregado tudo depois das 21h?",
    "Então qual seria a economia? Pode agendar para hoje às 22h?",
]


def main():
    llm = criar_llm()
    linhas = ["# Demonstração da memória por sessão", ""]

    def rodar(titulo, bot, sessao, perguntas):
        linhas.append(f"## {titulo}\n")
        print(f"\n=== {titulo} ===")
        for i, p in enumerate(perguntas, 1):
            r = bot.perguntar(p, sessao)
            h = bot.memoria.historico(sessao)
            print(
                f"[T{i}] Você: {p}\n     Bot: {r.texto}\n     (memória: {h.tokens_em_uso()} tokens, "
                f"{len(h.messages)} msgs; resumo: {'sim' if bot.memoria.resumo(sessao) else 'não'})"
            )
            linhas.extend(
                [
                    f"**T{i} - Usuário:** {p}",
                    "",
                    f"**Assistente:** {r.texto}",
                    "",
                    f"_memória: {h.tokens_em_uso()} tokens - {len(h.messages)} mensagens_",
                    "",
                ]
            )
        resumo = bot.memoria.resumo(sessao)
        if resumo:
            linhas.append(f"> **Resumo da sessão (mensagens que saíram da janela):** {resumo}")
            linhas.append("")

    bot = ChargeOpsAssistant(llm, "v3", limite_tokens_memoria=config.LIMITE_TOKENS_MEMORIA)
    rodar("Sessão apto202 (4 turnos encadeados)", bot, "apto202", TURNOS)
    rodar(
        "Sessão outra (isolamento: não deve saber do apto 202)",
        bot,
        "outra",
        ["Qual é o meu apartamento?"],
    )

    curto = ChargeOpsAssistant(llm, "v3", limite_tokens_memoria=350)
    rodar("Sessão curta (limite de 350 tokens: poda + resumo)", curto, "curta", TURNOS)

    destino = config.PASTA_EVALS / "demo_memoria.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nTranscrição salva em {destino.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
