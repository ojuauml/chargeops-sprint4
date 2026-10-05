import argparse

from src import config
from src.chain.builder import ChargeOpsAssistant, criar_llm, medir_tokens_prompt


def main():
    ap = argparse.ArgumentParser(description="ChargeOps Assistant (Sprint 03, LangChain LCEL)")
    ap.add_argument("--modelo", default=config.MODELO_PRINCIPAL)
    ap.add_argument("--prompt", default=config.VERSAO_PROMPT_PADRAO, choices=["v1", "v2", "v3"])
    ap.add_argument("--sem-guardrails", action="store_true")
    ap.add_argument("--json", action="store_true", help="exibe o ConsultaRecarga de cada resposta")
    args = ap.parse_args()

    llm = criar_llm(args.modelo)
    bot = ChargeOpsAssistant(llm, args.prompt, guardrails=not args.sem_guardrails)
    print("=" * 62)
    print(
        f"ChargeOps Assistant - {args.modelo} - prompt {args.prompt} - "
        f"guardrails {'OFF' if args.sem_guardrails else 'ON'}"
    )
    print(
        f"System prompt: {medir_tokens_prompt(args.prompt)} tokens - memória: "
        f"{config.LIMITE_TOKENS_MEMORIA} tokens"
    )
    print("Digite sua pergunta. Comandos: /novo - /tokens - sair")
    print("=" * 62)

    while True:
        try:
            pergunta = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break
        if pergunta.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            break
        if not pergunta:
            continue
        if pergunta == "/novo":
            bot.nova_sessao()
            print("(nova sessão)")
            continue
        if pergunta == "/tokens":
            h = bot.memoria.historico("padrao")
            print(f"(memória: {h.tokens_em_uso()} tokens em {len(h.messages)} mensagens)")
            continue
        r = bot.perguntar(pergunta)
        print("\nAssistente:", r.texto)
        if r.bloqueado_por:
            print(f"  [guardrail: {r.bloqueado_por}]")
        if args.json and r.consulta:
            print("  [json]", r.consulta.model_dump_json(indent=2, exclude={"resposta_usuario"}))
        if r.schema_ok is False:
            print(f"  [aviso: saída fora do schema - {r.erro_schema}]")
        print(
            f"  ({r.latencia_s:.1f}s - {r.uso.get('tokens_entrada', 0)} tokens in / "
            f"{r.uso.get('tokens_saida', 0)} out)"
        )


if __name__ == "__main__":
    main()
