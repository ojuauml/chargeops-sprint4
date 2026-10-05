import argparse

from src import config
from src.chain.builder import criar_llm
from src.rag.chain import RagAssistant


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default=config.MODELO_PRINCIPAL)
    ap.add_argument("--versao", default=config.VERSAO_RAG_PADRAO, choices=["v1", "v2"])
    ap.add_argument("--sem-guardrails", action="store_true")
    args = ap.parse_args()

    llm = criar_llm(args.modelo, temperature=0.0)
    assistente = RagAssistant(llm, versao=args.versao, guardrails=not args.sem_guardrails)
    print("=" * 62)
    print(
        f"ChargeOps RAG - {args.modelo} - prompt {args.versao} - guardrails {'OFF' if args.sem_guardrails else 'ON'}"
    )
    print("Digite sua pergunta sobre o condomínio. Digite sair para encerrar.")
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
        resultado = assistente.perguntar(pergunta)
        print("\nAssistente:", resultado.texto)
        if resultado.fontes:
            print("  fontes:")
            for fonte in resultado.fontes:
                print(
                    f"    - {fonte['documento']} ({fonte['secao']}, relevância {fonte['relevancia']:.2f})"
                )
        print(
            f"  (faithfulness {resultado.faithfulness} - answer relevancy {resultado.answer_relevancy} - "
            f"citação: {'sim' if resultado.citacao_presente else 'não'} - {resultado.latencia_s:.1f}s)"
        )


if __name__ == "__main__":
    main()
