import re

from src.guardrails.scope_validator import normalizar


def avaliar_caso(caso, resultado):
    checks = []
    for ck in caso.checks:
        achou = re.search(ck.padrao, normalizar(resultado.texto)) is not None
        ok = achou if ck.tipo == "contem" else not achou
        checks.append({"criterio": ck.descricao, "ok": ok})

    if caso.esperado_na_base:
        checks.append(
            {"criterio": "não ficou fora de contexto", "ok": not resultado.fora_do_contexto}
        )
        checks.append({"criterio": "cita a fonte", "ok": resultado.citacao_presente})
    else:
        checks.append(
            {"criterio": "recusou por estar fora de contexto", "ok": resultado.fora_do_contexto}
        )

    aprovados = sum(c["ok"] for c in checks)
    nota = round(10 * aprovados / len(checks), 2) if checks else 0.0
    return {
        "nota": nota,
        "checks_aprovados": aprovados,
        "checks_total": len(checks),
        "checks": checks,
        "faithfulness": resultado.faithfulness,
        "answer_relevancy": resultado.answer_relevancy,
        "citacao_presente": resultado.citacao_presente,
        "fora_do_contexto": resultado.fora_do_contexto,
        "linhas_neutralizadas": resultado.linhas_neutralizadas,
    }
