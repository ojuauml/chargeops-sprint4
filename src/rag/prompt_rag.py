from langchain_core.prompts import ChatPromptTemplate

from src import config


def carregar_prompt_rag(versao):
    return (config.PASTA_PROMPTS / f"rag_prompt_{versao}.md").read_text(encoding="utf-8")


def construir_prompt_rag(versao):
    return ChatPromptTemplate.from_messages([("human", carregar_prompt_rag(versao))])


def formatar_contexto(resultados):
    blocos = []
    for i, (documento, relevancia) in enumerate(resultados, 1):
        blocos.append(
            f"[{i}] Fonte: {documento.metadata['fonte_titulo']}, "
            f"seção: {documento.metadata['secao']} (relevância {relevancia:.2f})\n"
            f"{documento.page_content.strip()}"
        )
    return "\n\n".join(blocos) if blocos else "(nenhum trecho encontrado)"
