import json

from src import config
from src.rag.multi_provider import consulta_multipla_rag, montar_modelos

PERGUNTAS = [
    "Qual a tarifa no horário de pico?",
    "O que significa o código de erro E05?",
]


def main():
    modelos = montar_modelos()
    print(f"Modelos: {list(modelos)} | versões de prompt: v1, v2")
    resultados, md = {}, [
        "# Chamada multi-provider no RAG (bônus)",
        "",
        f"Modelos: {', '.join(modelos)} - versões: v1 e v2",
        "",
    ]
    for pergunta in PERGUNTAS:
        saida = consulta_multipla_rag(pergunta, modelos)
        resultados[pergunta] = saida
        md += [
            f"## {pergunta}",
            "",
            "| Ramo (modelo|versão) | Latência (s) | Citação | Faithfulness | Resposta |",
            "|---|---|---|---|---|",
        ]
        for ramo, r in saida.items():
            resposta = (r["erro"] and f"ERRO: {r['erro']}") or r["texto"].replace("\n", " ")
            md.append(
                f"| `{ramo}` | {r['latencia_s']} | {r['citacao_presente']} | {r['faithfulness']} | {resposta[:300]} |"
            )
            print(f"  {ramo:<35} {r['latencia_s']:>6}s  {'ERRO' if r['erro'] else 'ok'}")
        md.append("")
    (config.PASTA_EVALS / "multi_provider_rag_results.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (config.PASTA_EVALS / "multi_provider_rag_results.md").write_text(
        "\n".join(md), encoding="utf-8"
    )
    print("Salvo em evals/multi_provider_rag_results.{json,md}")


if __name__ == "__main__":
    main()
