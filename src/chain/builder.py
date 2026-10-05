import json
import re
import time
import warnings
from dataclasses import dataclass, field
from operator import itemgetter
from typing import Any, Optional

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory

try:
    from langchain_classic.output_parsers import OutputFixingParser
except ImportError:
    try:
        from langchain.output_parsers import OutputFixingParser
    except ImportError:
        OutputFixingParser = None

from src import config

from src.chain.memoria import GerenciadorMemoria
from src.chain.tokens import MedidorTokens, contar_tokens
from src.dados import BASE_CONHECIMENTO, CONTEXTO_API, HISTORICO_SESSOES
from src.guardrails import EstadoSessao, checar_entrada, moderar_saida
from src.schemas import FORMATO_SAIDA, ConsultaRecarga

warnings.filterwarnings(
    "ignore", message=".*(RunnableWithMessageHistory|ConversationTokenBufferMemory).*"
)

VERSOES = {
    "v1": {"estruturado": False, "json_compacto": False, "humano": "{pergunta}"},
    "v2": {"estruturado": True, "json_compacto": True, "humano": "{pergunta}"},
    "v3": {
        "estruturado": True,
        "json_compacto": True,
        "humano": "<pergunta_usuario>\n{pergunta}\n</pergunta_usuario>",
    },
}
_PLACEHOLDERS_LEGADO = {
    "{CONTEXT_API_GOODWE}": "{contexto_api}",
    "{CONTEXT_SESSION_HISTORY}": "{historico_sessoes}",
}


def _json(dados, compacto):
    if compacto:
        return json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(dados, ensure_ascii=False, indent=2)


def carregar_prompt(versao):
    if versao not in VERSOES:
        raise ValueError(f"versão de prompt desconhecida: {versao!r} (use {list(VERSOES)})")
    texto = (config.PASTA_PROMPTS / f"system_prompt_{versao}.md").read_text(encoding="utf-8")
    for antigo, novo in _PLACEHOLDERS_LEGADO.items():
        texto = texto.replace(antigo, novo)
    return texto


def _variaveis_dados(versao):
    compacto = VERSOES[versao]["json_compacto"]
    return {
        "contexto_api": _json(CONTEXTO_API, compacto),
        "historico_sessoes": _json(HISTORICO_SESSOES, compacto),
        "base_conhecimento": _json(BASE_CONHECIMENTO, compacto),
        "formato_saida": FORMATO_SAIDA,
    }


def renderizar_system_prompt(versao, resumo="", com_dados=True):
    texto = carregar_prompt(versao)
    valores = (
        _variaveis_dados(versao)
        if com_dados
        else {k: "" for k in ("contexto_api", "historico_sessoes", "base_conhecimento")}
        | {"formato_saida": FORMATO_SAIDA}
    )
    valores["resumo_conversa"] = resumo or "(sem resumo)"
    for chave, valor in valores.items():
        texto = texto.replace("{" + chave + "}", valor)
    return texto


def medir_tokens_prompt(versao):
    return contar_tokens(renderizar_system_prompt(versao))


def construir_prompt(versao):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", carregar_prompt(versao)),
            MessagesPlaceholder("historico"),
            ("human", VERSOES[versao]["humano"]),
        ]
    )
    return prompt.partial(**_variaveis_dados(versao))


def criar_llm(
    modelo=None,
    *,
    temperature=None,
    top_p=None,
    max_tokens=None,
    reasoning=None,
):
    from langchain_ollama import ChatOllama

    p = config.PARAMETROS_PADRAO
    kwargs = dict(
        model=modelo or config.MODELO_PRINCIPAL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=p["temperature"] if temperature is None else temperature,
        top_p=p["top_p"] if top_p is None else top_p,
        num_predict=p["max_tokens"] if max_tokens is None else max_tokens,
        custom_get_token_ids=lambda texto: [0] * contar_tokens(texto),
    )
    razao = reasoning or config.OLLAMA_REASONING
    if razao:
        kwargs["reasoning"] = razao
    if config.OLLAMA_API_KEY:
        kwargs["client_kwargs"] = {"headers": {"Authorization": f"Bearer {config.OLLAMA_API_KEY}"}}
    return ChatOllama(**kwargs)


_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _extrair_json(texto):
    texto = _RE_THINK.sub("", texto).strip()
    ini, fim = texto.find("{"), texto.rfind("}")
    return texto[ini : fim + 1] if ini != -1 and fim > ini else texto


def _resposta_de_emergencia(bruto):
    m = re.search(r'"resposta_usuario"\s*:\s*"((?:[^"\\]|\\.)*)"', bruto, re.DOTALL)
    if m:
        try:
            return json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            return m.group(1)
    return _RE_THINK.sub("", bruto).strip() or (
        "Desculpe, tive um problema para montar a resposta. Pode repetir a pergunta?"
    )


def construir_chain(llm, versao, estruturado=None):
    if estruturado is None:
        estruturado = VERSOES[versao]["estruturado"]
    if estruturado and not VERSOES[versao]["estruturado"]:
        raise ValueError(f"o prompt {versao} não define formato de saída estruturada")

    prompt = construir_prompt(versao)

    if not estruturado:
        gerar = prompt | llm | StrOutputParser()

        def _final_texto(d):
            return {"texto": d["texto"].strip(), "consulta": None, "erro_schema": None}

        return {"texto": gerar, "pergunta": itemgetter("pergunta")} | RunnableLambda(_final_texto)

    parser = PydanticOutputParser(pydantic_object=ConsultaRecarga)
    corrigidor = (
        OutputFixingParser.from_llm(llm=llm, parser=parser, max_retries=1)
        if OutputFixingParser is not None
        else parser
    )
    gerar = prompt | llm | StrOutputParser() | RunnableLambda(_extrair_json)

    def _final_estruturado(d, config):
        bruto = d["texto"]
        try:
            consulta = corrigidor.invoke(bruto, config=config)
            return {"texto": consulta.resposta_usuario, "consulta": consulta, "erro_schema": None}
        except (OutputParserException, ValueError) as erro:
            return {
                "texto": _resposta_de_emergencia(bruto),
                "consulta": None,
                "erro_schema": str(erro)[:300],
            }

    return {"texto": gerar, "pergunta": itemgetter("pergunta")} | RunnableLambda(_final_estruturado)


@dataclass
class Resultado:
    texto: str
    consulta: Optional[ConsultaRecarga] = None
    bloqueado_por: Optional[str] = None
    schema_ok: Optional[bool] = None
    schema_primeira_tentativa: Optional[bool] = None
    erro_schema: Optional[str] = None
    latencia_s: float = 0.0
    latencia_resumo_s: float = 0.0
    uso: dict[str, Any] = field(default_factory=dict)
    uso_resumo: dict[str, Any] = field(default_factory=dict)


class ChargeOpsAssistant:

    def __init__(
        self,
        llm,
        versao_prompt=config.VERSAO_PROMPT_PADRAO,
        *,
        estruturado=None,
        limite_tokens_memoria=config.LIMITE_TOKENS_MEMORIA,
        guardrails=True,
        resumir=True,
        llm_resumo=None,
    ):
        self.llm = llm
        self.versao = versao_prompt
        self.estruturado = (
            VERSOES[versao_prompt]["estruturado"] if estruturado is None else estruturado
        )
        self.guardrails = guardrails
        self.memoria = GerenciadorMemoria(
            llm, limite_tokens_memoria, resumir=resumir, llm_resumo=llm_resumo
        )
        self.chain = construir_chain(llm, versao_prompt, self.estruturado)
        self.chain_com_memoria = RunnableWithMessageHistory(
            self.chain,
            self.memoria.historico,
            input_messages_key="pergunta",
            history_messages_key="historico",
            output_messages_key="texto",
        )
        self._estados = {}
        self._instrucoes = renderizar_system_prompt(versao_prompt, com_dados=False)
        self._base_textos = [
            json.dumps(d, ensure_ascii=False)
            for d in (CONTEXTO_API, HISTORICO_SESSOES, BASE_CONHECIMENTO)
        ]

    def perguntar(self, pergunta, session_id="padrao"):
        inicio = time.perf_counter()

        if self.guardrails:
            estado = self._estados.setdefault(session_id, EstadoSessao())
            g = checar_entrada(pergunta, estado)
            if not g.permitido:
                return Resultado(
                    texto=g.resposta,
                    bloqueado_por=g.categoria,
                    latencia_s=time.perf_counter() - inicio,
                )

        medidor = MedidorTokens()
        saida = self.chain_com_memoria.invoke(
            {
                "pergunta": pergunta,
                "resumo_conversa": self.memoria.resumo(session_id) or "(sem resumo)",
            },
            config={"configurable": {"session_id": session_id}, "callbacks": [medidor]},
        )
        texto, consulta, erro = saida["texto"], saida["consulta"], saida["erro_schema"]
        latencia = time.perf_counter() - inicio

        bloqueado = None
        if self.guardrails:
            gs = moderar_saida(texto, self._instrucoes, self._base_textos, pergunta)
            if not gs.permitido:
                bloqueado, texto = gs.categoria, gs.resposta
                self.memoria.historico(session_id).substituir_ultima_resposta(texto)

        med_resumo = MedidorTokens()
        t_resumo = time.perf_counter()
        self.memoria.atualizar_resumo(session_id, config={"callbacks": [med_resumo]})
        latencia_resumo = time.perf_counter() - t_resumo if med_resumo.chamadas else 0.0

        estruturado_aplicavel = self.estruturado
        return Resultado(
            texto=texto,
            consulta=consulta,
            bloqueado_por=bloqueado,
            schema_ok=(consulta is not None) if estruturado_aplicavel else None,
            schema_primeira_tentativa=(
                (consulta is not None and medidor.chamadas == 1) if estruturado_aplicavel else None
            ),
            erro_schema=erro,
            latencia_s=latencia,
            latencia_resumo_s=latencia_resumo,
            uso=medidor.resumo(),
            uso_resumo=med_resumo.resumo(),
        )

    def nova_sessao(self, session_id="padrao"):
        self.memoria.limpar(session_id)
        self._estados.pop(session_id, None)
