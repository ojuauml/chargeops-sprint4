import json
import time

from src import config
from src.chain.tokens import contar_tokens
from src.dados import CONTEXTO_API, HISTORICO_SESSOES


def montar_system_prompt():
    prompt = (config.PASTA_PROMPTS / "system_prompt_v1.md").read_text(encoding="utf-8")
    prompt = prompt.replace(
        "{CONTEXT_API_GOODWE}", json.dumps(CONTEXTO_API, ensure_ascii=False, indent=2)
    )
    prompt = prompt.replace(
        "{CONTEXT_SESSION_HISTORY}", json.dumps(HISTORICO_SESSOES, ensure_ascii=False, indent=2)
    )
    return prompt


class ChatbotLegado:
    def __init__(
        self,
        base_url,
        api_key,
        modelo,
        temperature=0.3,
        max_tokens=None,
    ):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.modelo = modelo
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _responder(self, mensagens):
        kwargs = dict(model=self.modelo, messages=mensagens, temperature=self.temperature)
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens
        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or "", getattr(resp, "usage", None)

    def conversar(self, perguntas):
        mensagens = [{"role": "system", "content": montar_system_prompt()}]
        registros = []
        for pergunta in perguntas:
            mensagens.append({"role": "user", "content": pergunta})
            entrada = sum(contar_tokens(m["content"]) + 4 for m in mensagens)
            inicio = time.perf_counter()
            try:
                resposta, uso = self._responder(mensagens)
                erro = None
            except Exception as e:
                resposta, uso, erro = "", None, f"{type(e).__name__}: {e}"[:300]
            latencia = time.perf_counter() - inicio
            mensagens.append({"role": "assistant", "content": resposta})
            registros.append(
                {
                    "pergunta": pergunta,
                    "resposta": resposta,
                    "latencia_s": round(latencia, 3),
                    "tokens_entrada": entrada,
                    "tokens_saida": contar_tokens(resposta),
                    "tokens_entrada_provider": getattr(uso, "prompt_tokens", None),
                    "tokens_saida_provider": getattr(uso, "completion_tokens", None),
                    "chamadas_llm": 1,
                    "bloqueado_por": None,
                    "schema_ok": None,
                    "schema_primeira_tentativa": None,
                    "erro": erro,
                }
            )
        return registros
