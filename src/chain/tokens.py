import math

from langchain_core.callbacks import BaseCallbackHandler

_ENCODING = None
ENCODING_NOME = "estimativa (len/4)"
ESTIMATIVA = True


def _carregar():
    global _ENCODING, ENCODING_NOME, ESTIMATIVA
    if _ENCODING is not None or not ESTIMATIVA:
        return
    try:
        import tiktoken
    except ImportError:
        return
    for nome in ("o200k_harmony", "o200k_base", "cl100k_base"):
        try:
            _ENCODING = tiktoken.get_encoding(nome)
            ENCODING_NOME, ESTIMATIVA = nome, False
            return
        except Exception:
            continue


def contar_tokens(texto):
    _carregar()
    if _ENCODING is not None:
        return len(_ENCODING.encode(texto, disallowed_special=()))
    return math.ceil(len(texto) / 4)


def contar_tokens_mensagens(mensagens):
    return sum(contar_tokens(str(m.content)) + 4 for m in mensagens)


class MedidorTokens(BaseCallbackHandler):

    def __init__(self):
        self.entrada_tiktoken = 0
        self.saida_tiktoken = 0
        self.entrada_provider = None
        self.saida_provider = None
        self.chamadas = 0

    def on_chat_model_start(
        self,
        serialized,
        messages,
        *,
        run_id,
        **kwargs,
    ):
        self.chamadas += 1
        for lote in messages:
            self.entrada_tiktoken += contar_tokens_mensagens(lote)

    def on_llm_end(self, response, *, run_id, **kwargs):
        for lote in response.generations:
            for ger in lote:
                self.saida_tiktoken += contar_tokens(ger.text or "")
                msg = getattr(ger, "message", None)
                uso = getattr(msg, "usage_metadata", None)
                if uso:
                    self.entrada_provider = (self.entrada_provider or 0) + uso.get(
                        "input_tokens", 0
                    )
                    self.saida_provider = (self.saida_provider or 0) + uso.get("output_tokens", 0)

    def resumo(self):
        return {
            "tokens_entrada": self.entrada_tiktoken,
            "tokens_saida": self.saida_tiktoken,
            "tokens_entrada_provider": self.entrada_provider,
            "tokens_saida_provider": self.saida_provider,
            "chamadas_llm": self.chamadas,
        }
