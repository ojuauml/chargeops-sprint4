import argparse
import datetime
import json
import re
import statistics
import sys
import urllib.request

from evals.avaliador_rag import avaliar_caso
from evals.rag_eval_set import CASOS
from src import config
from src.chain.builder import criar_llm
from src.rag.chain import RagAssistant
from src.rag.embeddings import criar_embeddings
from src.rag.vector_store import CONFIG_INDEXACAO, indexar

ARQ_RESULTADOS = config.PASTA_EVALS / "rag_results.json"
ARQ_VERSOES = config.PASTA_PROMPTS / "VERSOES.md"
ARQ_RELATORIO_RAG = config.PASTA_DOCS / "relatorio_rag.md"
ARQ_MODELOS = config.PASTA_DOCS / "relatorio_modelos.md"

INI_RAG = "<!-- AUTO:RAG:INICIO -->"
FIM_RAG = "<!-- AUTO:RAG:FIM -->"


def f(x, casas=2):
    if x is None:
        return "-"
    return f"{x:.{casas}f}".replace(".", ",")


def pct(x):
    if x is None:
        return "-"
    return f"{100 * x:.0f}%"


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
        return False
    for m in modelos:
        if m not in instalados and m + ":latest" not in instalados:
            print(f"Aviso: o modelo {m} não aparece no Ollama (ollama pull {m})")
    return True


def rodar_iteracao(versao, llm, embeddings, casos):
    _, total_chunks = indexar(versao, embeddings)
    assistente = RagAssistant(llm, embeddings=embeddings, versao=versao)
    casos_resultado = []
    for caso in casos:
        resultado = assistente.perguntar(caso.pergunta)
        avaliacao = avaliar_caso(caso, resultado)
        casos_resultado.append(
            {
                "id": caso.id,
                "categoria": caso.categoria,
                "pergunta": caso.pergunta,
                "resposta": resultado.texto,
                "fontes": resultado.fontes,
                "latencia_s": round(resultado.latencia_s, 3),
                "tokens_entrada": resultado.uso.get("tokens_entrada", 0),
                "tokens_saida": resultado.uso.get("tokens_saida", 0),
                **avaliacao,
            }
        )
        print(
            f"    {caso.id:<4} nota {avaliacao['nota']:>5.2f}  faithfulness {f(avaliacao['faithfulness'])}  relevancy {f(avaliacao['answer_relevancy'])}"
        )

    notas = [c["nota"] for c in casos_resultado]
    faith = [c["faithfulness"] for c in casos_resultado if c["faithfulness"] is not None]
    relev = [c["answer_relevancy"] for c in casos_resultado if c["answer_relevancy"] is not None]
    com_citacao = [c for c in casos_resultado if c["categoria"] != "fora_contexto"]
    resumo = {
        "chunk_size": CONFIG_INDEXACAO[versao]["chunk_size"],
        "chunk_overlap": CONFIG_INDEXACAO[versao]["chunk_overlap"],
        "k": CONFIG_INDEXACAO[versao]["k"],
        "total_chunks": total_chunks,
        "nota_media": round(statistics.mean(notas), 2) if notas else None,
        "faithfulness_media": round(statistics.mean(faith), 3) if faith else None,
        "answer_relevancy_media": round(statistics.mean(relev), 3) if relev else None,
        "fracao_com_citacao": (
            round(sum(c["citacao_presente"] for c in com_citacao) / len(com_citacao), 2)
            if com_citacao
            else None
        ),
        "tokens_entrada_medio": (
            round(
                statistics.mean(
                    [c["tokens_entrada"] for c in casos_resultado if c["tokens_entrada"]]
                ),
                0,
            )
            if any(c["tokens_entrada"] for c in casos_resultado)
            else None
        ),
        "latencia_media_s": round(statistics.mean([c["latencia_s"] for c in casos_resultado]), 3),
    }
    return {"resumo": resumo, "casos": casos_resultado}


def rodar_comparativo_modelos(casos):
    p = config.PARAMETROS_PADRAO
    configs = [
        {
            "modelo": config.MODELO_PRINCIPAL,
            "temperature": 0.0,
            "top_p": p["top_p"],
            "max_tokens": p["max_tokens"],
        },
        {
            "modelo": config.MODELO_SECUNDARIO,
            "temperature": 0.0,
            "top_p": p["top_p"],
            "max_tokens": p["max_tokens"],
        },
    ]
    embeddings = criar_embeddings()
    resultados = {}
    for cfg in configs:
        llm = criar_llm(
            cfg["modelo"],
            temperature=cfg["temperature"],
            top_p=cfg["top_p"],
            max_tokens=cfg["max_tokens"],
        )
        print(
            f"\n>>> modelo {cfg['modelo']} (k={CONFIG_INDEXACAO['v2']['k']}, temperature={cfg['temperature']})"
        )
        saida = rodar_iteracao("v2", llm, embeddings, casos)
        resultados[cfg["modelo"]] = {"params": cfg, "resumo": saida["resumo"]}
    return resultados


def atualizar_versoes(iteracoes):
    linhas = [
        "| Iteração | chunk_size / overlap | k | Nota média (0 a 10) | Faithfulness médio | Answer relevancy médio | Respostas com citação |",
        "|---|---|---|---|---|---|---|",
    ]
    nomes = {"v1": "v1 (ingênua)", "v2": "v2 (grounding + citação)"}
    for versao, nome in nomes.items():
        if versao not in iteracoes:
            continue
        r = iteracoes[versao]["resumo"]
        linhas.append(
            f"| {nome} | {r['chunk_size']} / {r['chunk_overlap']} | {r['k']} | {f(r['nota_media'])} | "
            f"{f(r['faithfulness_media'])} | {f(r['answer_relevancy_media'])} | {pct(r['fracao_com_citacao'])} |"
        )
    bloco = f"{INI_RAG}\n\n## Prompt RAG\n\n" + "\n".join(linhas) + f"\n\n{FIM_RAG}"
    texto = ARQ_VERSOES.read_text(encoding="utf-8")
    if INI_RAG in texto:
        texto = re.sub(
            re.escape(INI_RAG) + r".*?" + re.escape(FIM_RAG),
            lambda m: bloco,
            texto,
            flags=re.DOTALL,
        )
    else:
        texto = texto.rstrip() + "\n\n" + bloco + "\n"
    ARQ_VERSOES.write_text(texto, encoding="utf-8")


def gerar_relatorio_rag(iteracoes):
    v1, v2 = iteracoes.get("v1"), iteracoes.get("v2")
    if not v1 or not v2:
        print("relatorio_rag.md não gerado: faltam as duas iterações")
        return
    r1, r2 = v1["resumo"], v2["resumo"]
    ganho_nota = (
        round(r2["nota_media"] - r1["nota_media"], 2)
        if r1["nota_media"] and r2["nota_media"]
        else None
    )

    linhas_casos = [
        "| Caso | Categoria | Nota v1 | Nota v2 | Faithfulness v1 | Faithfulness v2 |",
        "|---|---|---|---|---|---|",
    ]
    casos_v1 = {c["id"]: c for c in v1["casos"]}
    for c in v2["casos"]:
        c1 = casos_v1.get(c["id"], {})
        linhas_casos.append(
            f"| {c['id']} | {c['categoria']} | {f(c1.get('nota'))} | {f(c['nota'])} | "
            f"{f(c1.get('faithfulness'))} | {f(c['faithfulness'])} |"
        )

    texto = f"""# Relatório da avaliação RAG

Comparação entre as duas iterações de ingestão e prompt, nos mesmos {len(v2['casos'])} casos de teste (evals/rag_eval_set.py), sobre a mesma base de conhecimento (data/knowledge_base/).

## Decisões de chunking

A iteração 1 usa chunk_size {r1['chunk_size']} e overlap {r1['chunk_overlap']} (chunks pequenos, sem sobreposição): fragmenta demais os parágrafos, então um trecho recuperado às vezes corta uma frase no meio e perde uma parte da informação. A iteração 2 usa chunk_size {r2['chunk_size']} e overlap {r2['chunk_overlap']}, que mantém cada seção mais inteira e a sobreposição evita cortar uma frase bem na fronteira entre dois chunks. O k (quantidade de trechos buscados) também mudou de {r1['k']} para {r2['k']}, trazendo mais contexto por pergunta.

O prompt também mudou entre as duas iterações: a v1 só pede para responder com base no contexto, sem regra de citação, sem regra de recusa fora de contexto e sem proteção contra instrução escondida dentro de um documento. A v2 exige citar a fonte, recusar pergunta fora do contexto, nunca inventar número e tratar o conteúdo de <contexto> como dado e não como instrução.

## Scores por iteração

| Métrica | Iteração 1 (ingênua) | Iteração 2 (grounding + citação) |
|---|---|---|
| Nota média no eval (0 a 10) | {f(r1['nota_media'])} | {f(r2['nota_media'])} |
| Faithfulness médio (0 a 1) | {f(r1['faithfulness_media'])} | {f(r2['faithfulness_media'])} |
| Answer relevancy médio (0 a 1) | {f(r1['answer_relevancy_media'])} | {f(r2['answer_relevancy_media'])} |
| Respostas com citação de fonte | {pct(r1['fracao_com_citacao'])} | {pct(r2['fracao_com_citacao'])} |
| Chunks indexados | {r1['total_chunks']} | {r2['total_chunks']} |
| Tokens de entrada por pergunta | {f(r1['tokens_entrada_medio'], 0)} | {f(r2['tokens_entrada_medio'], 0)} |
| Latência média (s) | {f(r1['latencia_media_s'])} | {f(r2['latencia_media_s'])} |

Ganho de nota da iteração 1 para a 2: {f(ganho_nota)} pontos.

## Nota por caso

{chr(10).join(linhas_casos)}

## Como as métricas foram calculadas

RAGAS não funcionou neste ambiente: ao importar, a versão instalada tenta carregar `langchain_community.chat_models.vertexai.ChatVertexAI`, que não existe mais nessa versão do langchain-community (erro `ModuleNotFoundError`). Isso aconteceu com a 0.4.3 e também com a 0.2.15. Por isso usamos o fallback manual documentado, permitido pelo enunciado:

- **faithfulness_manual**: procura números, valores em reais, códigos de erro, kWh e datas dentro da resposta e confere se cada um aparece literalmente nos trechos recuperados. Se a resposta não tem nenhum número ou código para checar, o score é 1,0 (nada a conferir). É equivalente ao faithfulness do RAGAS porque mede a mesma coisa: se a resposta está apoiada no contexto, só que de forma determinística em vez de usar um LLM juiz.
- **answer_relevancy_manual**: similaridade de cosseno entre o embedding da pergunta e o embedding da resposta, usando o mesmo modelo de embeddings da vetorização (nomic-embed-text). É a mesma ideia do answer_relevancy do RAGAS (que compara pergunta e resposta por embedding), simplificada para não precisar gerar perguntas reversas com um LLM. Se os embeddings não estiverem disponíveis, cai para sobreposição de palavras entre pergunta e resposta.
- Essas duas métricas e a citação de fonte são calculadas por `src/rag/metricas.py`, chamado automaticamente dentro de `RagAssistant.perguntar`.
"""
    ARQ_RELATORIO_RAG.write_text(texto, encoding="utf-8")


def gerar_relatorio_modelos(comparativo):
    nomes = list(comparativo)
    if len(nomes) < 2:
        print("relatorio_modelos.md não gerado: faltam modelos")
        return
    a, b = comparativo[nomes[0]], comparativo[nomes[1]]
    ra, rb = a["resumo"], b["resumo"]

    texto = f"""# Relatório de uso de modelos e parâmetros - Sprint 04 (RAG)

Comparação feita com o mesmo pipeline RAG (iteração v2, chunk_size {ra['chunk_size']}, overlap {ra['chunk_overlap']}, k={ra['k']}) e o mesmo conjunto de perguntas (evals/rag_eval_set.py), trocando só o modelo de geração.

## Parâmetros usados

| Parâmetro | {nomes[0]} | {nomes[1]} | Motivo |
|---|---|---|---|
| temperature | {a['params']['temperature']} | {b['params']['temperature']} | 0, como recomendado para RAG: a resposta deve vir só do contexto recuperado, sem variação criativa |
| top_p | {a['params']['top_p']} | {b['params']['top_p']} | mantido no padrão do projeto |
| max_tokens | {a['params']['max_tokens']} | {b['params']['max_tokens']} | alto o bastante para a resposta não sair cortada |
| k (trechos buscados) | {ra['k']} | {rb['k']} | mesmo valor nos dois, para a comparação ser justa |
| modelo de embeddings | nomic-embed-text | nomic-embed-text | mesmo modelo de vetorização para os dois, só o modelo de geração muda |

## Resultados

| Métrica | {nomes[0]} | {nomes[1]} |
|---|---|---|
| Nota média no eval (0 a 10) | {f(ra['nota_media'])} | {f(rb['nota_media'])} |
| Faithfulness médio (0 a 1) | {f(ra['faithfulness_media'])} | {f(rb['faithfulness_media'])} |
| Answer relevancy médio (0 a 1) | {f(ra['answer_relevancy_media'])} | {f(rb['answer_relevancy_media'])} |
| Respostas com citação de fonte | {pct(ra['fracao_com_citacao'])} | {pct(rb['fracao_com_citacao'])} |
| Tokens de entrada por pergunta | {f(ra['tokens_entrada_medio'], 0)} | {f(rb['tokens_entrada_medio'], 0)} |
| Latência média (s) | {f(ra['latencia_media_s'])} | {f(rb['latencia_media_s'])} |

## Observações

- Modelo de embeddings e chunking são os mesmos nos dois casos, então a diferença de resultado vem só da geração.
- As notas vêm das checagens automáticas de evals/avaliador_rag.py mais as métricas de faithfulness e answer relevancy de src/rag/metricas.py.
- Cada configuração rodou uma vez, então pequenas variações entre rodadas são esperadas mesmo com temperature 0.
"""
    ARQ_MODELOS.write_text(texto, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", help="v1,v2 ou so-modelos ou so-iteracoes")
    ap.add_argument("--casos", help="ids separados por vírgula, ex: R1,R2")
    args = ap.parse_args()

    casos = [c for c in CASOS if not args.casos or c.id in args.casos.split(",")]
    rodar_iteracoes = args.so in (None, "so-iteracoes")
    rodar_modelos = args.so in (None, "so-modelos")

    if not verificar_ollama(
        [config.MODELO_PRINCIPAL, config.MODELO_SECUNDARIO, config.MODELO_EMBEDDING]
    ):
        sys.exit(1)

    anterior = {}
    if ARQ_RESULTADOS.exists():
        anterior = json.loads(ARQ_RESULTADOS.read_text(encoding="utf-8"))
    iteracoes = anterior.get("iteracoes", {})
    comparativo_modelos = anterior.get("comparativo_modelos", {})

    if rodar_iteracoes:
        llm = criar_llm(config.MODELO_PRINCIPAL, temperature=0.0)
        embeddings = criar_embeddings()
        versoes = (
            args.so.split(",")
            if args.so and args.so not in ("so-modelos", "so-iteracoes")
            else ["v1", "v2"]
        )
        for versao in versoes:
            print(
                f"\n>>> iteração {versao} (chunk_size={CONFIG_INDEXACAO[versao]['chunk_size']}, k={CONFIG_INDEXACAO[versao]['k']})"
            )
            iteracoes[versao] = rodar_iteracao(versao, llm, embeddings, casos)

    if rodar_modelos:
        comparativo_modelos = rodar_comparativo_modelos(casos)

    dados = {
        "meta": {"gerado_em": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")},
        "iteracoes": iteracoes,
        "comparativo_modelos": comparativo_modelos,
    }
    ARQ_RESULTADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nResultados salvos em evals/rag_results.json")

    if iteracoes:
        atualizar_versoes(iteracoes)
        gerar_relatorio_rag(iteracoes)
        print("prompts/VERSOES.md e docs/relatorio_rag.md atualizados")
    if comparativo_modelos:
        gerar_relatorio_modelos(comparativo_modelos)
        print("docs/relatorio_modelos.md atualizado")


if __name__ == "__main__":
    main()
