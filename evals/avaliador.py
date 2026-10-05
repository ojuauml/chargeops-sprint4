import re

from src.guardrails.scope_validator import normalizar


def avaliar(caso, respostas):
    textos = [normalizar(r or "") for r in respostas]
    detalhes = []
    for ck in caso.checks:
        try:
            alvo = textos[ck.turno]
        except IndexError:
            alvo = ""
        achou = re.search(ck.padrao, alvo) is not None
        ok = achou if ck.tipo == "contem" else not achou
        detalhes.append({"criterio": ck.descricao, "ok": ok})
    aprovadas = sum(d["ok"] for d in detalhes)
    return {
        "nota": round(10 * aprovadas / len(detalhes), 2) if detalhes else 0.0,
        "checks_aprovados": aprovadas,
        "checks_total": len(detalhes),
        "checks": detalhes,
    }
