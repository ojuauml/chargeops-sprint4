CONTEXTO_API = {
    "mes_referencia": "maio/2026",
    "estacoes": [
        {"id": "CHR-001", "status": "disponivel"},
        {"id": "CHR-002", "status": "em_uso", "previsao_liberacao": "19:45"},
        {
            "id": "CHR-003",
            "status": "erro",
            "codigo_erro": "E05",
            "descricao": "GroundFailure",
            "ultima_falha": "18/05/2026 14:32",
            "ultima_sessao_ok": "17/05/2026 09:15",
            "ocorrencias_ultimos_7_dias": 4,
        },
        {"id": "CHR-004", "status": "disponivel"},
    ],
    "ocupacao_por_horario": {
        "18h": {"ocupacao": "85%", "tarifa": 1.30},
        "19h": {"ocupacao": "90%", "tarifa": 1.30},
        "20h": {"ocupacao": "78%", "tarifa": 1.30},
        "21h": {"ocupacao": "45%", "tarifa": 0.75},
        "22h": {"ocupacao": "20%", "tarifa": 0.75},
        "23h": {"ocupacao": "10%", "tarifa": 0.75},
    },
    "consumo_apartamentos": {
        "101": {"kwh_total": 52.4, "sessoes": 18},
        "202": {"kwh_total": 31.1, "sessoes": 9, "kwh_fora_pico": 22.9, "kwh_pico": 8.2},
        "303": {"kwh_total": 67.8, "sessoes": 24},
        "404": {"kwh_total": 12.0, "sessoes": 4},
    },
    "taxa_infraestrutura_mensal": 80.00,
}

HISTORICO_SESSOES = [
    {
        "id": "S-1042",
        "unidade": "202",
        "inicio": "18/05/2026 19:10",
        "fim": "18/05/2026 20:05",
        "kwh": 6.4,
        "kw": 7.0,
        "status": "concluida",
        "carregador": "CHR-001",
    },
    {
        "id": "S-1041",
        "unidade": "101",
        "inicio": "18/05/2026 14:00",
        "fim": "18/05/2026 15:30",
        "kwh": 9.8,
        "kw": 7.0,
        "status": "concluida",
        "carregador": "CHR-002",
    },
    {
        "id": "S-1040",
        "unidade": "303",
        "inicio": "18/05/2026 14:20",
        "fim": "18/05/2026 14:32",
        "kwh": 0.0,
        "kw": 0.0,
        "status": "erro",
        "carregador": "CHR-003",
    },
]

BASE_CONHECIMENTO = {
    "E05": {
        "descricao": "GroundFailure (falha de aterramento / corrente de fuga para a terra)",
        "checklist_tecnico_habilitado": [
            "1. Isolar o circuito do carregador (desenergizar e sinalizar antes de qualquer intervenção)",
            "2. Medir a continuidade do condutor PE (aterramento) entre o carregador e o quadro",
            "3. Verificar o DR (dispositivo diferencial residual) do circuito do CHR-003",
            "4. Se a falha persistir, abrir chamado no suporte técnico da GoodWe",
        ],
        "observacao": "Procedimento somente para profissional habilitado (NR-10). Risco de choque elétrico.",
    }
}
