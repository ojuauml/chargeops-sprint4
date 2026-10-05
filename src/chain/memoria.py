from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

try:
    from langchain_classic.memory import ConversationTokenBufferMemory
except ImportError:
    from langchain.memory import ConversationTokenBufferMemory

from src.config import LIMITE_TOKENS_MEMORIA


class MemoriaSessao(BaseChatMessageHistory):

    def __init__(self, llm, max_token_limit):
        self._memoria = ConversationTokenBufferMemory(
            llm=llm, max_token_limit=max_token_limit, return_messages=True
        )
        self.descartadas = []

    @property
    def messages(self):
        return list(self._memoria.chat_memory.messages)

    def add_messages(self, messages):
        antes = list(self._memoria.chat_memory.messages)
        humanas = [m for m in messages if isinstance(m, HumanMessage)]
        ias = [m for m in messages if isinstance(m, AIMessage)]
        if len(messages) == 2 and len(humanas) == 1 and len(ias) == 1:
            self._memoria.save_context(
                {"input": str(humanas[0].content)}, {"output": str(ias[0].content)}
            )
        else:
            for m in messages:
                self._memoria.chat_memory.add_message(m)
        total = antes + list(messages)
        depois = self._memoria.chat_memory.messages
        podadas = len(total) - len(depois)
        if podadas > 0:
            self.descartadas.extend(total[:podadas])

    def clear(self):
        self._memoria.chat_memory.clear()
        self.descartadas.clear()

    def substituir_ultima_resposta(self, texto):
        msgs = self._memoria.chat_memory.messages
        for m in reversed(msgs):
            if isinstance(m, AIMessage):
                m.content = texto
                return

    def tokens_em_uso(self):
        return self._memoria.llm.get_num_tokens_from_messages(self.messages)


_PROMPT_RESUMO = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você resume conversas de suporte de um condomínio com carregadores de veículos "
            "elétricos. Atualize o resumo abaixo incorporando os novos trechos. Guarde SÓ fatos "
            "úteis para continuar o atendimento: quem é o usuário (persona/apartamento), o que "
            "já foi perguntado, valores já calculados e pendências (ex.: confirmação de "
            "agendamento). No máximo 100 palavras, em português, sem inventar nada.",
        ),
        (
            "human",
            "<resumo_anterior>\n{resumo_anterior}\n</resumo_anterior>\n\n"
            "<novos_trechos>\n{trechos}\n</novos_trechos>\n\nResumo atualizado:",
        ),
    ]
)


def construir_chain_resumo(llm):
    return _PROMPT_RESUMO | llm | StrOutputParser()


class GerenciadorMemoria:

    def __init__(
        self,
        llm,
        limite_tokens=LIMITE_TOKENS_MEMORIA,
        resumir=True,
        llm_resumo=None,
    ):
        self._llm = llm
        self.limite_tokens = limite_tokens
        self.resumir = resumir
        self._chain_resumo = construir_chain_resumo(llm_resumo or llm) if resumir else None
        self._sessoes = {}
        self._resumos = {}

    def historico(self, session_id):
        if session_id not in self._sessoes:
            self._sessoes[session_id] = MemoriaSessao(self._llm, self.limite_tokens)
        return self._sessoes[session_id]

    def resumo(self, session_id):
        return self._resumos.get(session_id, "")

    def atualizar_resumo(self, session_id, config=None):
        if not self.resumir or self._chain_resumo is None:
            return False
        hist = self.historico(session_id)
        if not hist.descartadas:
            return False
        trechos = "\n".join(
            f"{'Usuário' if isinstance(m, HumanMessage) else 'Assistente'}: {m.content}"
            for m in hist.descartadas
        )
        self._resumos[session_id] = self._chain_resumo.invoke(
            {"resumo_anterior": self.resumo(session_id) or "(vazio)", "trechos": trechos},
            config=config,
        ).strip()
        hist.descartadas.clear()
        return True

    def limpar(self, session_id=None):
        if session_id is None:
            self._sessoes.clear()
            self._resumos.clear()
        else:
            self._sessoes.pop(session_id, None)
            self._resumos.pop(session_id, None)
