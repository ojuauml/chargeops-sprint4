import statistics as st

from evals.avaliador import avaliar
from evals.baseline_legacy import ChatbotLegado
from evals.eval_set import CASOS, IDS_COMPARAVEIS
from src import config
from src.chain.builder import ChargeOpsAssistant, criar_llm
from src.chain.tokens import ENCODING_NOME


def _media(valores):
    return round(st.mean(valores), 3) if valores else None


def resumir(casos_res):
    turnos = [t for c in casos_res for t in c["turnos"]]
    com_llm = [t for t in turnos if not t.get("bloqueado_por") and not t.get("erro")]
    estruturados = [t for t in com_llm if t.get("schema_ok") is not None]
    por_cat = {}
    for c in casos_res:
        por_cat.setdefault(c["categoria"], []).append(c["nota"])
    comparaveis = [c["nota"] for c in casos_res if c["id"] in IDS_COMPARAVEIS]
    return {
        "nota_media_total": _media([c["nota"] for c in casos_res]),
        "nota_media_comparavel_sprint12": _media(comparaveis),
        "nota_por_categoria": {k: _media(v) for k, v in por_cat.items()},
        "casos_nota_10": sum(c["nota"] >= 9.995 for c in casos_res),
        "casos_total": len(casos_res),
        "turnos_total": len(turnos),
        "turnos_com_llm": len(com_llm),
        "turnos_bloqueados_guardrail": sum(bool(t.get("bloqueado_por")) for t in turnos),
        "turnos_com_erro": sum(bool(t.get("erro")) for t in turnos),
        "tokens_entrada_por_turno": _media([t["tokens_entrada"] for t in com_llm]),
        "tokens_saida_por_turno": _media([t["tokens_saida"] for t in com_llm]),
        "tokens_total_por_turno": _media(
            [t["tokens_entrada"] + t["tokens_saida"] for t in com_llm]
        ),
        "tokens_entrada_por_turno_provider": _media(
            [t["tokens_entrada_provider"] for t in com_llm if t.get("tokens_entrada_provider")]
        ),
        "latencia_media_s": _media([t["latencia_s"] for t in com_llm]),
        "chamadas_llm_por_turno": _media([t["chamadas_llm"] for t in com_llm]),
        "acuracia_structured_primeira_tentativa": (
            _media([1.0 if t["schema_primeira_tentativa"] else 0.0 for t in estruturados])
            if estruturados
            else None
        ),
        "acuracia_structured_final": (
            _media([1.0 if t["schema_ok"] else 0.0 for t in estruturados]) if estruturados else None
        ),
        "tokenizador": ENCODING_NOME,
    }


def _executar_casos(casos, rodar_caso, progresso):
    saida = []
    for caso in casos:
        turnos = rodar_caso(caso)
        av = avaliar(caso, [t["resposta"] for t in turnos])
        saida.append(
            {
                "id": caso.id,
                "categoria": caso.categoria,
                "origem": caso.origem,
                "persona": caso.persona,
                "turnos": turnos,
                **av,
            }
        )
        if progresso:
            print(
                f"    {caso.id:<4} nota {av['nota']:>5.2f}  ({av['checks_aprovados']}/{av['checks_total']})"
            )
    return saida


def rodar_legado(cfg, casos=CASOS, progresso=True):
    p = cfg["params"]
    bot = ChatbotLegado(
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        modelo=cfg["modelo"],
        temperature=p.get("temperature", 0.3),
        max_tokens=p.get("max_tokens"),
    )
    res = _executar_casos(casos, lambda c: bot.conversar(c.turnos), progresso)
    return {
        "config": {k: v for k, v in cfg.items() if k != "api_key"},
        "resumo": resumir(res),
        "casos": res,
    }


def rodar_lcel(cfg, casos=CASOS, progresso=True):
    p = cfg["params"]
    llm = criar_llm(
        cfg["modelo"], temperature=p["temperature"], top_p=p["top_p"], max_tokens=p["max_tokens"]
    )
    assistente = ChargeOpsAssistant(
        llm,
        cfg["prompt"],
        guardrails=cfg["guardrails"],
        limite_tokens_memoria=cfg.get("limite_tokens_memoria", config.LIMITE_TOKENS_MEMORIA),
    )

    def rodar_caso(caso):
        sessao = f"{cfg['rotulo']}-{caso.id}"
        assistente.nova_sessao(sessao)
        registros = []
        for pergunta in caso.turnos:
            try:
                r = assistente.perguntar(pergunta, sessao)
                registros.append(
                    {
                        "pergunta": pergunta,
                        "resposta": r.texto,
                        "latencia_s": round(r.latencia_s, 3),
                        "tokens_entrada": r.uso.get("tokens_entrada", 0),
                        "tokens_saida": r.uso.get("tokens_saida", 0),
                        "tokens_entrada_provider": r.uso.get("tokens_entrada_provider"),
                        "tokens_saida_provider": r.uso.get("tokens_saida_provider"),
                        "chamadas_llm": r.uso.get("chamadas_llm", 0),
                        "bloqueado_por": r.bloqueado_por,
                        "schema_ok": r.schema_ok,
                        "schema_primeira_tentativa": r.schema_primeira_tentativa,
                        "erro": None,
                        "erro_schema": r.erro_schema,
                        "latencia_resumo_s": round(r.latencia_resumo_s, 3),
                    }
                )
            except Exception as e:
                registros.append(
                    {
                        "pergunta": pergunta,
                        "resposta": "",
                        "latencia_s": 0.0,
                        "tokens_entrada": 0,
                        "tokens_saida": 0,
                        "chamadas_llm": 0,
                        "bloqueado_por": None,
                        "schema_ok": None,
                        "schema_primeira_tentativa": None,
                        "erro": f"{type(e).__name__}: {e}"[:300],
                    }
                )
        return registros

    res = _executar_casos(casos, rodar_caso, progresso)
    return {"config": cfg, "resumo": resumir(res), "casos": res}
