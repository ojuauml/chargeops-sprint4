import argparse
import datetime
import json
import os
import re
import sys
import urllib.request

from evals.eval_set import CASOS, IDS_COMPARAVEIS
from evals.run_eval import rodar_lcel, rodar_legado
from src import config
from src.chain.builder import medir_tokens_prompt
from src.chain.tokens import ENCODING_NOME

ARQ_RESULTADOS = config.PASTA_EVALS / "sprint3_results.json"
ARQ_VERSOES = config.PASTA_PROMPTS / "VERSOES.md"
ARQ_MODELOS = config.PASTA_DOCS / "relatorio_modelos.md"


def definir_execucoes(usar_groq):
    p = dict(config.PARAMETROS_PADRAO)
    url_openai = config.OLLAMA_BASE_URL.rstrip("/") + "/v1"
    chave = config.OLLAMA_API_KEY or "ollama"

    def lcel(rotulo, prompt, guardrails, modelo=config.MODELO_PRINCIPAL):
        return {
            "rotulo": rotulo,
            "sistema": "lcel",
            "provedor": "ollama",
            "modelo": modelo,
            "prompt": prompt,
            "guardrails": guardrails,
            "params": p,
        }

    execucoes = [
        {
            "rotulo": "legado_ollama",
            "sistema": "legacy",
            "provedor": "ollama",
            "modelo": config.MODELO_PRINCIPAL,
            "base_url": url_openai,
            "api_key": chave,
            "params": {"temperature": 0.3, "max_tokens": p["max_tokens"]},
        },
        lcel("lcel_v1", "v1", False),
        lcel("lcel_v2", "v2", False),
        lcel("lcel_v3", "v3", False),
        lcel("lcel_v3_guardrails", "v3", True),
        lcel("lcel_v3_guardrails_qwen3", "v3", True, config.MODELO_SECUNDARIO),
    ]
    if usar_groq and os.getenv("GROQ_API_KEY"):
        execucoes.insert(
            1,
            {
                "rotulo": "legado_groq",
                "sistema": "legacy",
                "provedor": "groq",
                "modelo": config.GROQ_MODELO,
                "base_url": config.GROQ_BASE_URL,
                "api_key": os.environ["GROQ_API_KEY"],
                "params": {"temperature": 0.3},
            },
        )
    return execucoes


def f(x, casas=2):
    if x is None:
        return "-"
    return f"{x:.{casas}f}".replace(".", ",")


def pct(x):
    if x is None:
        return "-"
    return f"{100 * x:.0f}%"


def atualizar_versoes(execs):
    linhas = [
        "| Versão | Tokens do prompt | Nota C1-C7 | Nota total | Tokens de entrada/turno | Schema válido (1ª tentativa) | Latência (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    nomes = [
        ("legado_ollama", "v1 (código manual)"),
        ("lcel_v1", "v1 (LCEL)"),
        ("lcel_v2", "v2"),
        ("lcel_v3", "v3"),
        ("lcel_v3_guardrails", "v3 + guardrails"),
    ]
    for rotulo, nome in nomes:
        e = execs.get(rotulo)
        if not e:
            continue
        r = e["resumo"]
        versao = e["config"].get("prompt", "v1")
        linhas.append(
            f"| {nome} | {medir_tokens_prompt(versao)} | {f(r['nota_media_comparavel_sprint12'])} | "
            f"{f(r['nota_media_total'])} | {f(r['tokens_entrada_por_turno'], 0)} | "
            f"{pct(r['acuracia_structured_primeira_tentativa'])} | {f(r['latencia_media_s'])} |"
        )
    linhas.append("")
    linhas.append(f"Tokens contados com {ENCODING_NOME}.")
    bloco = "<!-- AUTO:INICIO -->\n" + "\n".join(linhas) + "\n<!-- AUTO:FIM -->"
    texto = ARQ_VERSOES.read_text(encoding="utf-8")
    novo = re.sub(
        r"<!-- AUTO:INICIO -->.*?<!-- AUTO:FIM -->",
        lambda m: bloco,
        texto,
        flags=re.DOTALL,
    )
    ARQ_VERSOES.write_text(novo, encoding="utf-8")


def gerar_relatorio_modelos(execs):
    a = execs.get("lcel_v3_guardrails")
    b = execs.get("lcel_v3_guardrails_qwen3")
    if not a or not b:
        print("relatorio_modelos.md não foi gerado (faltam execuções)")
        return
    colunas = [(a["config"]["modelo"], a), (b["config"]["modelo"], b)]
    g = execs.get("legado_groq")
    if g:
        colunas.append(("llama 3.3 70b (groq, código antigo)", g))

    def linha(nome, chave, formato=f):
        valores = [formato(c["resumo"][chave]) for _, c in colunas]
        return f"| {nome} | " + " | ".join(valores) + " |"

    cabecalho = "| Métrica | " + " | ".join(n for n, _ in colunas) + " |\n"
    cabecalho += "|---|" + "---|" * len(colunas)
    pa = a["config"]["params"]
    pb = b["config"]["params"]
    ra = a["resumo"]
    rb = b["resumo"]

    obs = []
    dif = ra["nota_media_total"] - rb["nota_media_total"]
    if abs(dif) < 0.005:
        obs.append(f"Os dois modelos tiraram a mesma nota ({f(ra['nota_media_total'])}).")
    else:
        melhor = colunas[0][0] if dif > 0 else colunas[1][0]
        obs.append(
            f"Nota média: {colunas[0][0]} = {f(ra['nota_media_total'])} e "
            f"{colunas[1][0]} = {f(rb['nota_media_total'])}. O {melhor} foi melhor por {f(abs(dif))} pontos."
        )
    if ra["latencia_media_s"] and rb["latencia_media_s"]:
        obs.append(
            f"Latência média por turno: {f(ra['latencia_media_s'])}s contra {f(rb['latencia_media_s'])}s."
        )
    if ra["acuracia_structured_primeira_tentativa"] is not None:
        obs.append(
            f"JSON válido na primeira tentativa: {pct(ra['acuracia_structured_primeira_tentativa'])} "
            f"contra {pct(rb['acuracia_structured_primeira_tentativa'])}."
        )

    categorias = sorted(set(ra["nota_por_categoria"]) | set(rb["nota_por_categoria"]))
    tabela_cat = "| Categoria | " + colunas[0][0] + " | " + colunas[1][0] + " |\n|---|---|---|\n"
    for c in categorias:
        tabela_cat += f"| {c} | {f(ra['nota_por_categoria'].get(c))} | {f(rb['nota_por_categoria'].get(c))} |\n"

    texto = (
        f"""# Relatório de modelos e parâmetros - Sprint 03

Comparação feita com o sistema final (LCEL + prompt v3 + guardrails), o mesmo conjunto de {ra['casos_total']} casos e os mesmos parâmetros nos dois modelos.

## Parâmetros usados

| Parâmetro | {a['config']['modelo']} | {b['config']['modelo']} | Motivo |
|---|---|---|---|
| temperature | {pa['temperature']} | {pb['temperature']} | baixa para os cálculos de tarifa darem sempre o mesmo resultado (igual na Sprint 2) |
| top_p | {pa['top_p']} | {pb['top_p']} | corta as palavras muito improváveis sem deixar o texto travado |
| max_tokens | {pa['max_tokens']} | {pb['max_tokens']} | alto porque modelos de raciocínio gastam tokens pensando e a resposta pode vir cortada |
| memória | {config.LIMITE_TOKENS_MEMORIA} tokens | {config.LIMITE_TOKENS_MEMORIA} tokens | limite do ConversationTokenBufferMemory |

## Resultados

{cabecalho}
{linha('Nota média C1-C7 (0 a 10)', 'nota_media_comparavel_sprint12')}
{linha('Nota média total (0 a 10)', 'nota_media_total')}
{linha('Casos com nota 10', 'casos_nota_10', str)}
{linha('Tokens de entrada por turno', 'tokens_entrada_por_turno', lambda x: f(x, 0))}
{linha('Tokens de saída por turno', 'tokens_saida_por_turno', lambda x: f(x, 0))}
{linha('Latência média por turno (s)', 'latencia_media_s')}
{linha('JSON válido na 1ª tentativa', 'acuracia_structured_primeira_tentativa', pct)}
{linha('JSON válido depois do retry', 'acuracia_structured_final', pct)}
{linha('Turnos bloqueados por guardrail', 'turnos_bloqueados_guardrail', str)}
{linha('Turnos com erro', 'turnos_com_erro', str)}

## Nota por categoria

{tabela_cat}
## Observações

"""
        + "\n".join(f"- {o}" for o in obs)
        + f"""

## Como as notas foram calculadas

- A nota de cada caso vem de checagens automáticas (regex) baseadas no modelo_de_teste.md, em evals/eval_set.py.
- Os tokens foram contados com {ENCODING_NOME}, então servem para comparar os modelos entre si.
- Cada configuração foi rodada uma vez, entao pode ter pequena variação de uma rodada para outra.
"""
    )
    ARQ_MODELOS.write_text(texto, encoding="utf-8")


def verificar_ollama(modelos):
    url = config.OLLAMA_BASE_URL.rstrip("/") + "/api/tags"
    req = urllib.request.Request(url)
    if config.OLLAMA_API_KEY:
        req.add_header("Authorization", "Bearer " + config.OLLAMA_API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            instalados = {m["name"] for m in json.loads(resp.read()).get("models", [])}
    except Exception as e:
        print("Não consegui conectar no Ollama em", config.OLLAMA_BASE_URL, "-", e)
        print("Abra o Ollama (ollama serve) ou confira o OLLAMA_BASE_URL no .env")
        return False
    for m in modelos:
        if m not in instalados and m + ":latest" not in instalados:
            print(f"Aviso: o modelo {m} não aparece no Ollama (ollama pull {m})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", help="rotulos separados por virgula")
    ap.add_argument("--casos", help="ids separados por virgula, ex: C1,C2")
    ap.add_argument("--sem-groq", action="store_true")
    args = ap.parse_args()

    casos = [c for c in CASOS if not args.casos or c.id in args.casos.split(",")]
    execucoes = definir_execucoes(not args.sem_groq)
    if args.so:
        escolhidas = args.so.split(",")
        execucoes = [e for e in execucoes if e["rotulo"] in escolhidas]

    modelos = sorted({e["modelo"] for e in execucoes if e["provedor"] == "ollama"})
    if modelos and not verificar_ollama(modelos):
        sys.exit(1)

    resultados = {}
    if ARQ_RESULTADOS.exists():
        resultados = json.loads(ARQ_RESULTADOS.read_text(encoding="utf-8"))["execucoes"]

    print("Casos:", len(casos), "| tokenizador:", ENCODING_NOME)
    if "estimativa" in ENCODING_NOME:
        print("Aviso: o tiktoken não baixou o vocabulário, os tokens são estimativas.")

    for cfg in execucoes:
        print("\n>>>", cfg["rotulo"], cfg["modelo"])
        try:
            if cfg["sistema"] == "legacy":
                resultados[cfg["rotulo"]] = rodar_legado(cfg, casos)
            else:
                resultados[cfg["rotulo"]] = rodar_lcel(cfg, casos)
        except Exception as e:
            print("Falhou:", e)
            continue
        r = resultados[cfg["rotulo"]]["resumo"]
        print(
            f"nota C1-C7 {f(r['nota_media_comparavel_sprint12'])} | nota total {f(r['nota_media_total'])} | "
            f"tokens/turno {f(r['tokens_total_por_turno'], 0)} | latencia {f(r['latencia_media_s'])}s | erros {r['turnos_com_erro']}"
        )

    nota_s2 = round(10 * (4 * 1 + 3 * 0.5) / 7, 2)
    meta = {
        "gerado_em": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "tokenizador": ENCODING_NOME,
        "casos_comparaveis": IDS_COMPARAVEIS,
        "sprint2_avaliacao_manual": {
            "adequada": 4,
            "parcial": 3,
            "inadequada": 0,
            "nota_equivalente_0a10": nota_s2,
        },
    }
    dados = {"meta": meta, "execucoes": resultados}
    ARQ_RESULTADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nResultados salvos em evals/sprint3_results.json")

    atualizar_versoes(resultados)
    gerar_relatorio_modelos(resultados)
    print("prompts/VERSOES.md e docs/relatorio_modelos.md atualizados")


if __name__ == "__main__":
    main()
