import json

from src import config
from src.chain.multi_provider import consulta_multipla, montar_provedores

PERGUNTAS = [
    "quanto vou pagar de recarga esse mês? eu sou do apto 202",
    "o carregador CHR-003 está com problema, o que está acontecendo?",
]


def main():
    provedores = montar_provedores()
    print(f"Provedores: {list(provedores)} | prompts: v1, v3")
    resultados, md = {}, [
        "# Chamada multi-provider (bônus)",
        "",
        f"Provedores: {', '.join(provedores)} - prompts: v1 e v3",
        "",
    ]
    for pergunta in PERGUNTAS:
        saida = consulta_multipla(pergunta, provedores)
        resultados[pergunta] = saida
        md += [
            f"## {pergunta}",
            "",
            "| Ramo (provedor\\|prompt) | Latência (s) | Schema | Resposta |",
            "|---|---|---|---|",
        ]
        for ramo, r in saida.items():
            resposta = (r["erro"] and f"ERRO: {r['erro']}") or r["texto"].replace("\n", " ")
            md.append(f"| `{ramo}` | {r['latencia_s']} | {r['schema_ok']} | {resposta[:400]} |")
            print(f"  {ramo:<45} {r['latencia_s']:>6}s  {'ERRO' if r['erro'] else 'ok'}")
        md.append("")
    (config.PASTA_EVALS / "multi_provider_results.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (config.PASTA_EVALS / "multi_provider_results.md").write_text("\n".join(md), encoding="utf-8")
    print("Salvo em evals/multi_provider_results.{json,md}")


if __name__ == "__main__":
    main()
