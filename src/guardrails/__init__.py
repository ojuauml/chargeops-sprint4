from .moderation import moderar_entrada, moderar_saida
from .rag_injection import neutralizar
from .scope_validator import (
    EstadoSessao,
    ResultadoGuardrail,
    atualizar_estado,
    detectar_injecao,
    validar_escopo,
    validar_privacidade,
)


def checar_entrada(texto, estado):
    atualizar_estado(texto, estado)
    for etapa in (detectar_injecao, moderar_entrada, validar_escopo):
        r = etapa(texto)
        if not r.permitido:
            return r
    return validar_privacidade(texto, estado)


__all__ = [
    "EstadoSessao",
    "ResultadoGuardrail",
    "atualizar_estado",
    "checar_entrada",
    "detectar_injecao",
    "moderar_entrada",
    "moderar_saida",
    "neutralizar",
    "validar_escopo",
    "validar_privacidade",
]
