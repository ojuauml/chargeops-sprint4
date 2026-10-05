import re
import unicodedata
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TARIFAS_VALIDAS = (0.75, 0.95, 1.30)
POTENCIA_MAXIMA_KW = 22.0
TOLERANCIA_FATURAMENTO = 0.05


class EstadoCarregador(str, Enum):
    DISPONIVEL = "disponivel"
    EM_USO = "em_uso"
    ERRO = "erro"
    DESCONHECIDO = "desconhecido"

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None
        chave = _sem_acento(value).strip().lower().replace("-", "_").replace(" ", "_")
        apelidos = {
            "livre": cls.DISPONIVEL,
            "ocupado": cls.EM_USO,
            "em_uso": cls.EM_USO,
            "falha": cls.ERRO,
            "fora_do_ar": cls.ERRO,
            "indisponivel": cls.ERRO,
        }
        if chave in apelidos:
            return apelidos[chave]
        for membro in cls:
            if membro.value == chave:
                return membro
        return None


class Intencao(str, Enum):
    CONSULTA_STATUS = "consulta_status"
    CONSUMO_CUSTO = "consumo_custo"
    MELHOR_HORARIO = "melhor_horario"
    RESUMO_CONSUMO = "resumo_consumo"
    RATEIO = "rateio"
    FALHA_TECNICA = "falha_tecnica"
    AGENDAMENTO = "agendamento"
    FORA_DE_ESCOPO = "fora_de_escopo"
    RECUSA_SEGURANCA = "recusa_seguranca"
    OUTRO = "outro"


class Persona(str, Enum):
    MORADOR = "morador"
    SINDICO = "sindico"
    GESTOR = "gestor"
    TECNICO = "tecnico"
    DESCONHECIDA = "desconhecida"


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _para_numero(valor):
    if valor is None or isinstance(valor, (int, float)):
        return valor
    if isinstance(valor, str):
        texto = re.sub(r"[^\d,.\-]", "", valor)
        if texto in ("", "-"):
            return None
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        return float(texto)
    return valor


class ConsultaRecarga(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    intencao: Intencao = Field(description="O que o usuário quer")
    persona: Persona = Field(default=Persona.DESCONHECIDA, description="Quem está falando")
    carregador_id: Optional[str] = Field(default=None, description="Ex.: CHR-003")
    estado_carregador: Optional[EstadoCarregador] = None
    potencia_kw: Optional[float] = Field(default=None, description="Potência em kW")
    energia_kwh: Optional[float] = Field(default=None, description="Energia em kWh")
    tarifa_aplicada: Optional[float] = Field(default=None, description="R$/kWh")
    faturamento_rs: Optional[float] = Field(default=None, description="Valor em R$")
    unidade: Optional[str] = Field(default=None, description="Apartamento, ex.: 202")
    requer_confirmacao: bool = Field(default=False)
    escopo_ok: bool = Field(default=True, description="False se fora do escopo/recusa")
    resposta_usuario: str = Field(min_length=1, description="Texto final ao usuário")

    @field_validator("carregador_id", mode="before")
    @classmethod
    def _normaliza_carregador(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        texto = str(v).strip().upper().replace(" ", "-").replace("_", "-")
        if re.fullmatch(r"CHR\d{3}", texto):
            texto = f"CHR-{texto[3:]}"
        if not re.fullmatch(r"CHR-\d{3}", texto):
            raise ValueError(f"carregador_id inválido: {v!r} (esperado CHR-000)")
        return texto

    @field_validator("potencia_kw", mode="before")
    @classmethod
    def _potencia_numero(cls, v):
        return _para_numero(v)

    @field_validator("potencia_kw")
    @classmethod
    def _potencia_faixa(cls, v):
        if v is not None and not (0 <= v <= POTENCIA_MAXIMA_KW):
            raise ValueError(f"potencia_kw fora da faixa 0–{POTENCIA_MAXIMA_KW}: {v}")
        return v

    @field_validator("energia_kwh", "faturamento_rs", mode="before")
    @classmethod
    def _valores_numero(cls, v):
        return _para_numero(v)

    @field_validator("energia_kwh", "faturamento_rs")
    @classmethod
    def _nao_negativo(cls, v):
        if v is not None and v < 0:
            raise ValueError("valor não pode ser negativo")
        return None if v is None else round(v, 2)

    @field_validator("tarifa_aplicada", mode="before")
    @classmethod
    def _tarifa_numero(cls, v):
        return _para_numero(v)

    @field_validator("tarifa_aplicada")
    @classmethod
    def _tarifa_existente(cls, v):
        if v is None:
            return v
        if not any(abs(v - t) < 1e-6 for t in TARIFAS_VALIDAS):
            raise ValueError(f"tarifa {v} não existe (válidas: {TARIFAS_VALIDAS})")
        return v

    @field_validator("unidade", mode="before")
    @classmethod
    def _unidade_normaliza(cls, v):
        if v is None:
            return None
        digitos = re.sub(r"\D", "", str(v))
        return digitos or None

    @field_validator("unidade")
    @classmethod
    def _unidade_formato(cls, v):
        if v is not None and not re.fullmatch(r"\d{2,4}", v):
            raise ValueError(f"unidade inválida: {v!r}")
        return v

    @model_validator(mode="after")
    def _coerencia(self):
        if None not in (self.energia_kwh, self.tarifa_aplicada, self.faturamento_rs):
            esperado = self.energia_kwh * self.tarifa_aplicada
            if abs(esperado - self.faturamento_rs) > TOLERANCIA_FATURAMENTO:
                raise ValueError(
                    f"faturamento incoerente: {self.energia_kwh} kWh x "
                    f"R$ {self.tarifa_aplicada} = {esperado:.2f}, veio {self.faturamento_rs}"
                )
        if not self.escopo_ok and self.faturamento_rs is not None:
            raise ValueError("resposta fora de escopo não deve trazer faturamento")
        return self


FORMATO_SAIDA = """Responda SOMENTE com um objeto JSON válido (sem markdown, sem texto antes ou depois), com estes campos:
- "intencao": um de consulta_status | consumo_custo | melhor_horario | resumo_consumo | rateio | falha_tecnica | agendamento | fora_de_escopo | recusa_seguranca | outro
- "persona": um de morador | sindico | gestor | tecnico | desconhecida
- "carregador_id": string no formato CHR-000, ou null
- "estado_carregador": disponivel | em_uso | erro | desconhecido, ou null
- "potencia_kw": número ou null (só se existir nos dados)
- "energia_kwh": número ou null
- "tarifa_aplicada": 0.75, 0.95 ou 1.30 (só quando houver UMA única tarifa), senão null
- "faturamento_rs": número em reais ou null
- "unidade": número do apartamento (ex.: "202") ou null
- "requer_confirmacao": true se você está pedindo confirmação antes de agendar/alterar algo
- "escopo_ok": false se a pergunta estiver fora do escopo ou tiver sido recusada
- "resposta_usuario": o texto completo que o usuário vai ler, em português, seguindo todas as regras
Use ponto como separador decimal nos números do JSON. Dentro de "resposta_usuario", use vírgula (ex.: R$ 27,84)."""
