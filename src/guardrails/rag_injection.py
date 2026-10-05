import re
import unicodedata

from langchain_core.documents import Document

_PADROES = [
    r"\b(ignor\w*|desconsider\w*|descart\w*|esqueca|esquece)\b.{0,30}\b(instruc\w+|regras|prompt|restric\w+)",
    r"\b(a partir de agora voce|voce agora e|finja|finge|aja como|atue como|assuma o papel)\b",
    r"\b(modo (desenvolvedor|deus|livre|sem restric\w+|debug|admin)|developer mode|jailbreak|dan\b)",
    r"\b(revele|mostre|exiba|repita|copie)\b.{0,30}\b(prompt|instruc\w+ (que|voce))",
    r"(<\|?\s*(im_start|im_end|system)\s*\|?>|\[/?inst\]|###\s*system)",
]
_PADROES_COMPILADOS = [re.compile(p) for p in _PADROES]

MARCADOR = "[trecho removido: continha um possível comando escondido no documento]"


def _normalizar(texto):
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.lower()


def _linha_suspeita(linha):
    norm = _normalizar(linha)
    return any(padrao.search(norm) for padrao in _PADROES_COMPILADOS)


def neutralizar(chunks):
    limpos = []
    linhas_removidas = 0
    for documento, relevancia in chunks:
        linhas = documento.page_content.split("\n")
        novas_linhas = []
        for linha in linhas:
            if _linha_suspeita(linha):
                novas_linhas.append(MARCADOR)
                linhas_removidas += 1
            else:
                novas_linhas.append(linha)
        texto_limpo = "\n".join(novas_linhas)
        novo_doc = Document(page_content=texto_limpo, metadata=dict(documento.metadata))
        limpos.append((novo_doc, relevancia))
    return limpos, linhas_removidas
