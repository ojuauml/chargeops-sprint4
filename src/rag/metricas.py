import math
import re
import unicodedata

_PADROES_AFIRMACAO = [
    re.compile(r"r\$\s?\d+[,.]\d{2}"),
    re.compile(r"\d+[,.]\d+\s?kwh"),
    re.compile(r"\d+[,.]\d+\s?kw\b"),
    re.compile(r"\be0\d\b"),
    re.compile(r"\bchr-?\d{3}\b"),
    re.compile(r"\b\d{1,2}h\d{0,2}\b"),
    re.compile(r"\d+%"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
]


def _normalizar(texto):
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.lower()


def extrair_afirmacoes(texto):
    norm = _normalizar(texto)
    afirmacoes = []
    for padrao in _PADROES_AFIRMACAO:
        afirmacoes.extend(padrao.findall(norm))
    return list(dict.fromkeys(afirmacoes))


def faithfulness_manual(resposta, chunks):
    base = _normalizar(" ".join(documento.page_content for documento, _ in chunks))
    afirmacoes = extrair_afirmacoes(resposta)
    if not afirmacoes:
        return 1.0
    achadas = sum(1 for a in afirmacoes if a in base)
    return round(achadas / len(afirmacoes), 3)


def _cosseno(a, b):
    produto = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return produto / (norma_a * norma_b)


def answer_relevancy_manual(embeddings, pergunta, resposta):
    try:
        vetores = embeddings.embed_documents([pergunta, resposta])
        cos = _cosseno(vetores[0], vetores[1])
        return round(max(0.0, min(1.0, (cos + 1) / 2)), 3)
    except Exception:
        palavras_p = set(_normalizar(pergunta).split())
        palavras_r = set(_normalizar(resposta).split())
        if not palavras_p or not palavras_r:
            return 0.0
        intersecao = palavras_p & palavras_r
        uniao = palavras_p | palavras_r
        return round(len(intersecao) / len(uniao), 3)


def tem_citacao(resposta):
    return bool(re.search(r"\[fonte\s*:", resposta.lower()))
