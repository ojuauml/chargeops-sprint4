import os
import time

from langchain_core.runnables import RunnableLambda, RunnableParallel

from src import config
from src.chain.builder import construir_chain, criar_llm
from src.chain.tokens import contar_tokens
from src.guardrails import EstadoSessao, checar_entrada


def montar_provedores():
    provedores = {
        f"ollama:{config.MODELO_PRINCIPAL}": criar_llm(config.MODELO_PRINCIPAL),
        f"ollama:{config.MODELO_SECUNDARIO}": criar_llm(config.MODELO_SECUNDARIO),
    }
    if os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq

        p = config.PARAMETROS_PADRAO
        provedores[f"groq:{config.GROQ_MODELO}"] = ChatGroq(
            model=config.GROQ_MODELO,
            temperature=p["temperature"],
            max_tokens=p["max_tokens"],
            model_kwargs={"top_p": p["top_p"]},
            custom_get_token_ids=lambda t: [0] * contar_tokens(t),
        )
    return provedores


def _ramo(chain):

    def executar(entrada, config):
        t0 = time.perf_counter()
        try:
            saida = chain.invoke(entrada, config=config)
            return {
                "texto": saida["texto"],
                "schema_ok": (
                    (saida["consulta"] is not None)
                    if saida["consulta"] is not None or saida["erro_schema"]
                    else None
                ),
                "latencia_s": round(time.perf_counter() - t0, 2),
                "erro": None,
            }
        except Exception as e:
            return {
                "texto": "",
                "schema_ok": None,
                "latencia_s": round(time.perf_counter() - t0, 2),
                "erro": f"{type(e).__name__}: {e}"[:200],
            }

    return RunnableLambda(executar)


def consulta_multipla(
    pergunta,
    provedores=None,
    versoes=("v1", "v3"),
    guardrails=True,
):
    if guardrails:
        g = checar_entrada(pergunta, EstadoSessao())
        if not g.permitido:
            return {
                "(guardrail)": {
                    "texto": g.resposta,
                    "latencia_s": 0.0,
                    "schema_ok": None,
                    "erro": None,
                    "bloqueado_por": g.categoria,
                }
            }
    provedores = provedores or montar_provedores()
    ramos = {
        f"{nome}|{versao}": _ramo(construir_chain(llm, versao))
        for nome, llm in provedores.items()
        for versao in versoes
    }
    entrada = {"pergunta": pergunta, "historico": [], "resumo_conversa": "(sem resumo)"}
    return RunnableParallel(steps__=ramos).invoke(entrada)
