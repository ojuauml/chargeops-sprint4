import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResultadoGuardrail:
    permitido: bool
    categoria: Optional[str] = None
    motivo: str = ""
    resposta: str = ""
    avisos: list[str] = field(default_factory=list)


def normalizar(texto):
    sem = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem.lower()).strip()


RECUSA_FORA_ESCOPO = (
    "Essa pergunta foge um pouco do que eu faço por aqui, que é cuidar das recargas e "
    "estações do seu condomínio. Posso te ajudar a ver seu consumo do mês, conferir se "
    "tem estação livre ou agendar uma recarga. Quer alguma dessas?"
)
RECUSA_INJECAO = (
    "Não posso atender a esse tipo de pedido: minhas instruções e regras de funcionamento "
    "não mudam durante a conversa. Posso te ajudar com o que é do meu escopo: consumo, "
    "custo, rateio, status das estações, agendamento de recargas ou falhas nos "
    "carregadores. Por onde quer começar?"
)
RECUSA_PRIVACIDADE = (
    "Não posso compartilhar dados de outra unidade - cada morador só vê o próprio consumo. "
    "Se você for o síndico ou administrador, me diga e eu mostro a visão geral do condomínio. "
    "Posso mostrar o consumo da sua unidade?"
)

_PADROES_INJECAO = [
    (
        "jailbreak",
        "pedido para ignorar instruções",
        r"\b(ignor\w*|desconsider\w*|descart\w*)\b.{0,30}\b(instruc\w+|regras|diretrizes|orientac\w+|prompt|restric\w+|tudo (que|o que))",
    ),
    (
        "jailbreak",
        "pedido para esquecer instruções",
        r"\b(esqueca|esquece|esquecam)\b.{0,30}\b(tudo|instruc\w+|regras|diretrizes|prompt|o que (te |lhe )?(disseram|falaram|mandaram))",
    ),
    (
        "prompt_leak",
        "pedido para revelar o prompt/instruções",
        r"\b(system ?prompt|prompt (do|de) sistema|prompt inicial|seu prompt|suas instruc\w+|instruc\w+ (internas|iniciais|do sistema|originais)|regras internas)\b",
    ),
    (
        "prompt_leak",
        "pedido para revelar o prompt (verbo + alvo)",
        r"\b(revel\w+|mostr\w+|exib\w+|imprim\w+|repit\w+|copi\w+|vaz\w+|traduz\w+|resum\w+)\b.{0,40}\b(prompt|instruc\w+ (que|voce)|configurac\w+ interna)",
    ),
    (
        "jailbreak",
        "pedido de troca de papel",
        r"\b(finja|finge|pretenda|aja como|atue como|haja como|faca de conta|assuma o papel|a partir de agora voce (e|sera|vai ser|vai agir|deve agir|nao tem|nao precisa|pode ignorar)|voce agora e|voce deixou de ser|novo papel)\b",
    ),
    (
        "jailbreak",
        "modo sem restrições / DAN",
        r"(\bdan\b|do anything now|modo (desenvolvedor|deus|livre|sem restric\w+|debug|admin)|developer mode|jailbreak|sem (nenhuma |qualquer )?(restric\w+|filtros?|limites?|censura|regras))",
    ),
    (
        "jailbreak",
        "falsa autoridade (dev/admin do sistema)",
        r"\b(sou|eu sou|aqui e|estou falando como)\b.{0,15}\b(desenvolvedor|programador|administrador do sistema|dono do sistema|criador|engenheiro da (openai|anthropic|goodwe)|equipe de (ti|desenvolvimento))\b",
    ),
    (
        "injecao_marcadores",
        "marcadores de papel/tags do prompt",
        r"(<\|?\s*(im_start|im_end|system|assistant|endoftext)\s*\|?>|\[/?inst\]|###\s*(system|instruc)|(^| )system ?:|</?\s*(papel|contexto_sistema|personas|capacidades|restricoes|regras_comportamento|escopo|seguranca|dados_api|historico_sessoes|base_conhecimento|resumo_conversa|formato_saida|pergunta_usuario)\s*>)",
    ),
    (
        "prompt_leak",
        "extração por codificação",
        r"\b(base64|rot13|hexadecimal|em codigo morse)\b.{0,40}\b(prompt|instruc\w+|regras)",
    ),
]
_INJECAO_COMPILADA = [(c, m, re.compile(p)) for c, m, p in _PADROES_INJECAO]


def detectar_injecao(texto):
    norm = normalizar(texto)
    for categoria, motivo, padrao in _INJECAO_COMPILADA:
        if padrao.search(norm):
            return ResultadoGuardrail(False, categoria, motivo, RECUSA_INJECAO)
    return ResultadoGuardrail(True)


_DOMINIO = re.compile(
    r"(recarg|carreg|estac|eletropost|\bchr-?\d|apto|apart|unidade|kwh|\bkw\b|consum|tarifa|"
    r"rateio|sindic|sessao|sessoes|agend|horario|\bpico\b|falha|\berro\b|ocpp|goodwe|fatura|"
    r"condomin|\btaxa|infraestrutura|morador|tecnic|disjuntor|aterr|relatorio|custo|pagar|"
    r"gasto|economi|potencia|chargeops|wallbox|concession|energia|conta de luz|manutenc)"
)
_FORA_ESCOPO = re.compile(
    r"(\b(melhor|qual|que|indica\w*|recomend\w+)\b.{0,25}\b(carro|veiculo|modelo|marca|celular|notebook|tv|smartphone)s?\b.{0,25}\b(comprar|adquirir|pra comprar|para comprar|de 20\d\d|em 20\d\d)|"
    r"\bcomprar (um |uma )?(carro|veiculo|celular|notebook|casa|apartamento)\b|"
    r"\b(receita|ingredientes?) (de|do|da)\b|"
    r"\b(futebol|campeonato|placar|jogo do|copa do mundo|nba|formula 1)\b|"
    r"\b(eleicao|eleicoes|presidente|governador|partido politico|politica)\b|"
    r"\b(previsao do tempo|vai chover|clima em)\b|"
    r"\b(piada|poema|poesia|letra de musica|musica do|filme|serie|novela)\b|"
    r"\b(escreva|crie|faca|gere)\b.{0,20}\b(codigo|script|programa|funcao|redacao|texto sobre|resumo do livro)\b|"
    r"\b(capital d[aeo]|quem descobriu|quem inventou|quem ganhou|quantos habitantes)\b|"
    r"\b(horoscopo|signo|namorad[oa]|relacionamento|dieta|emagrecer|remedio)\b)"
)


def validar_escopo(texto):
    norm = normalizar(texto)
    if _FORA_ESCOPO.search(norm) and not _DOMINIO.search(norm):
        return ResultadoGuardrail(
            False, "fora_escopo", "assunto fora do ChargeOps", RECUSA_FORA_ESCOPO
        )
    return ResultadoGuardrail(True)


_RE_UNIDADE_PROPRIA = re.compile(
    r"\b(?:sou|moro|eu sou)\b.{0,15}\b(?:apto|apt|apartamento|ap|unidade)\.?\s*(\d{2,4})\b"
)
_RE_UNIDADE_PROPRIA_2 = re.compile(
    r"\b(?:apto|apt|apartamento|ap|unidade)\.?\s*(\d{2,4})\s*(?:aqui|falando)\b"
)
_RE_SINDICO = re.compile(
    r"\b(sou|eu sou|aqui e|falando como)\b.{0,12}\b(sindic\w+|administrador\w*|gestor\w*|zelador\w*)\b|\bsindico (aqui|falando)\b"
)
_RE_UNIDADES_CITADAS = re.compile(r"\b(?:apto|apt|apartamento|ap|unidade)\.?\s*(\d{2,4})\b")


@dataclass
class EstadoSessao:

    unidade: Optional[str] = None
    privilegiado: bool = False


def atualizar_estado(texto, estado):
    norm = normalizar(texto)
    if _RE_SINDICO.search(norm):
        estado.privilegiado = True
    m = _RE_UNIDADE_PROPRIA.search(norm) or _RE_UNIDADE_PROPRIA_2.search(norm)
    if m and not estado.privilegiado:
        estado.unidade = m.group(1)


def validar_privacidade(texto, estado):
    if estado.privilegiado or estado.unidade is None:
        return ResultadoGuardrail(True)
    citadas = set(_RE_UNIDADES_CITADAS.findall(normalizar(texto)))
    outras = citadas - {estado.unidade}
    if outras:
        return ResultadoGuardrail(
            False,
            "privacidade",
            f"unidade {estado.unidade} pediu dados da(s) unidade(s) {sorted(outras)}",
            RECUSA_PRIVACIDADE,
        )
    return ResultadoGuardrail(True)
