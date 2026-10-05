import time
from dataclasses import dataclass, field
from typing import Optional

from langchain_core.output_parsers import StrOutputParser

from src import config
from src.chain.tokens import MedidorTokens
from src.guardrails.rag_injection import neutralizar
from src.rag.embeddings import criar_embeddings
from src.rag.metricas import answer_relevancy_manual, faithfulness_manual, tem_citacao
from src.rag.prompt_rag import construir_prompt_rag, formatar_contexto
from src.rag.retriever import buscar
from src.rag.vector_store import CONFIG_INDEXACAO, obter_vector_store

RECUSA_FORA_CONTEXTO = (
    "Não encontrei isso na base de conhecimento do condomínio. Pode reformular a pergunta ou, "
    "se for algo urgente, fale com a portaria ou abra um chamado para a administradora."
)


@dataclass
class ResultadoRag:
    texto: str
    fontes: list = field(default_factory=list)
    fora_do_contexto: bool = False
    citacao_presente: bool = False
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    linhas_neutralizadas: int = 0
    latencia_s: float = 0.0
    uso: dict = field(default_factory=dict)


class RagAssistant:
    def __init__(
        self,
        llm,
        embeddings=None,
        versao=config.VERSAO_RAG_PADRAO,
        k=None,
        limiar_grounding=None,
        guardrails=True,
        store=None,
    ):
        self.llm = llm
        self.versao = versao
        self.embeddings = embeddings or criar_embeddings()
        self.k = k or CONFIG_INDEXACAO[versao]["k"]
        self.limiar = config.LIMIAR_GROUNDING if limiar_grounding is None else limiar_grounding
        self.guardrails = guardrails
        self.store = store or obter_vector_store(versao, self.embeddings)
        self.prompt = construir_prompt_rag(versao)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def perguntar(self, pergunta):
        inicio = time.perf_counter()
        resultados = buscar(self.store, pergunta, self.k)
        melhor = resultados[0][1] if resultados else 0.0
        linhas_neutralizadas = 0
        if self.guardrails and resultados:
            resultados, linhas_neutralizadas = neutralizar(resultados)

        if not resultados or melhor < self.limiar:
            return ResultadoRag(
                texto=RECUSA_FORA_CONTEXTO,
                fora_do_contexto=True,
                linhas_neutralizadas=linhas_neutralizadas,
                latencia_s=time.perf_counter() - inicio,
            )

        contexto = formatar_contexto(resultados)
        medidor = MedidorTokens()
        texto = self.chain.invoke(
            {"contexto": contexto, "pergunta": pergunta}, config={"callbacks": [medidor]}
        ).strip()

        fontes = [
            {
                "documento": documento.metadata["fonte_titulo"],
                "secao": documento.metadata["secao"],
                "relevancia": round(relevancia, 3),
            }
            for documento, relevancia in resultados
        ]
        return ResultadoRag(
            texto=texto,
            fontes=fontes,
            citacao_presente=tem_citacao(texto),
            faithfulness=faithfulness_manual(texto, resultados),
            answer_relevancy=answer_relevancy_manual(self.embeddings, pergunta, texto),
            linhas_neutralizadas=linhas_neutralizadas,
            latencia_s=time.perf_counter() - inicio,
            uso=medidor.resumo(),
        )
