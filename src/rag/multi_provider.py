import time

from langchain_core.runnables import RunnableLambda, RunnableParallel

from src import config
from src.chain.builder import criar_llm
from src.rag.chain import RagAssistant
from src.rag.embeddings import criar_embeddings
from src.rag.vector_store import obter_vector_store


def montar_modelos():
    return {
        config.MODELO_PRINCIPAL: criar_llm(config.MODELO_PRINCIPAL, temperature=0.0),
        config.MODELO_SECUNDARIO: criar_llm(config.MODELO_SECUNDARIO, temperature=0.0),
    }


def _ramo(modelo, embeddings, versao, store):
    def executar(entrada):
        inicio = time.perf_counter()
        try:
            assistente = RagAssistant(modelo, embeddings=embeddings, versao=versao, store=store)
            resultado = assistente.perguntar(entrada["pergunta"])
            return {
                "texto": resultado.texto,
                "fontes": resultado.fontes,
                "citacao_presente": resultado.citacao_presente,
                "faithfulness": resultado.faithfulness,
                "latencia_s": round(time.perf_counter() - inicio, 2),
                "erro": None,
            }
        except Exception as e:
            return {
                "texto": "",
                "fontes": [],
                "citacao_presente": None,
                "faithfulness": None,
                "latencia_s": round(time.perf_counter() - inicio, 2),
                "erro": f"{type(e).__name__}: {e}"[:200],
            }

    return RunnableLambda(executar)


def consulta_multipla_rag(pergunta, modelos=None, versoes=("v1", "v2")):
    modelos = modelos or montar_modelos()
    embeddings = criar_embeddings()
    stores = {versao: obter_vector_store(versao, embeddings) for versao in versoes}
    ramos = {
        f"{nome}|{versao}": _ramo(modelo, embeddings, versao, stores[versao])
        for nome, modelo in modelos.items()
        for versao in versoes
    }
    return RunnableParallel(steps__=ramos).invoke({"pergunta": pergunta})
