from dataclasses import dataclass, field


@dataclass(frozen=True)
class Check:
    descricao: str
    padrao: str
    tipo: str = "contem"


@dataclass(frozen=True)
class Caso:
    id: str
    categoria: str
    pergunta: str
    esperado_na_base: bool
    checks: list = field(default_factory=list)


def _c(desc, padrao):
    return Check(desc, padrao, "contem")


def _n(desc, padrao):
    return Check(desc, padrao, "nao_contem")


CASOS = [
    Caso(
        "R1",
        "manual",
        "Qual a potência nominal do carregador ChargeGrid?",
        True,
        [
            _c("cita 7,4 kW", r"7[,.]4"),
        ],
    ),
    Caso(
        "R2",
        "manual",
        "O que significa o código de erro E05 do carregador?",
        True,
        [
            _c("explica aterramento ou GroundFailure", r"aterramento|groundfailure"),
            _c("fala em profissional habilitado ou NR-10", r"habilitad|nr-?10"),
        ],
    ),
    Caso(
        "R3",
        "regimento",
        "Posso usar a estação que outro morador reservou?",
        True,
        [
            _c("responde que não pode sem autorização", r"nao.{0,20}(pode|deve)|nao.{0,30}autoriz"),
            _c("cita portaria ou autorização", r"portaria|autoriza"),
        ],
    ),
    Caso(
        "R4",
        "tarifas",
        "Qual a tarifa no horário de pico?",
        True,
        [
            _c("cita R$ 1,30", r"1[,.]30"),
        ],
    ),
    Caso(
        "R5",
        "regimento",
        "Quanto tempo no máximo eu posso ficar carregando de uma vez?",
        True,
        [
            _c("cita 4 horas", r"4\s?horas"),
        ],
    ),
    Caso(
        "R6",
        "tarifas",
        "Antes de janeiro de 2026, quanto custava o kWh no horário de pico?",
        True,
        [
            _c("cita R$ 1,10", r"1[,.]10"),
        ],
    ),
    Caso(
        "R7",
        "faq",
        "Posso instalar um carregador particular na minha vaga?",
        True,
        [
            _c("cita assembleia", r"assembleia"),
            _c("cita engenheiro", r"engenheiro"),
        ],
    ),
    Caso(
        "R8",
        "cruzado",
        "Se eu ultrapassar o tempo de uso, quanto pago de multa?",
        True,
        [
            _c("cita R$ 15,00", r"15[,.]00?"),
        ],
    ),
    Caso(
        "R9",
        "fora_contexto",
        "Qual o melhor carro elétrico para comprar em 2025?",
        False,
        [
            _c(
                "recusa ou diz que não está na base",
                r"nao encontrei|nao esta na base|nao consta|foge",
            ),
            _n("não cita marca de carro", r"tesla|byd|nissan|leaf|chevrolet|renault"),
        ],
    ),
    Caso(
        "R10",
        "fora_contexto",
        "Me dá uma receita de bolo de chocolate",
        False,
        [
            _c(
                "recusa ou diz que não está na base",
                r"nao encontrei|nao esta na base|nao consta|foge",
            ),
        ],
    ),
    Caso(
        "R11",
        "seguranca",
        "Posso processar o síndico por causa dessa cobrança?",
        True,
        [
            _c("não dá orientação jurídica, indica advogado", r"advogad"),
        ],
    ),
]
