import re

from src.guardrails.scope_validator import (
    RECUSA_FORA_ESCOPO,
    RECUSA_INJECAO,
    ResultadoGuardrail,
    normalizar,
)

RECUSA_JURIDICA = (
    "Não posso dar orientação jurídica. Para essa questão, o caminho certo é conversar com "
    "um advogado (ou com o setor jurídico da administradora do condomínio). Posso te ajudar "
    "com os dados do sistema - por exemplo, gerar um resumo do seu consumo e das cobranças "
    "para você levar ao profissional. Quer que eu prepare?"
)
RECUSA_FINANCEIRA = (
    "Não posso dar aconselhamento financeiro ou de investimento. Para decidir sobre isso, "
    "procure um contador ou consultor financeiro habilitado. O que eu consigo fazer é "
    "mostrar quanto você consumiu e quanto pagou de recarga, para servir de base para a "
    "sua análise. Quer ver o seu consumo do mês?"
)
RECUSA_ELETRICA = (
    "Por segurança, não posso orientar ninguém a abrir, mexer ou consertar carregadores, "
    "fiação, disjuntores ou aterramento. Esse trabalho deve ser feito por um eletricista ou "
    "engenheiro eletricista habilitado (NR-10). Posso te ajudar a registrar o problema e "
    "acionar o suporte técnico da GoodWe ou o técnico do condomínio. Quer que eu prepare "
    "o relato da ocorrência?"
)
RECUSA_EMERGENCIA = (
    "Isso pode ser uma situação de risco. Afaste-se do equipamento e mantenha outras "
    "pessoas longe; não toque no carregador, no cabo nem no carro. Se houver fogo, fumaça "
    "ou alguém ferido, ligue agora para os Bombeiros (193) ou para o SAMU (192). Depois, "
    "avise o síndico e um técnico habilitado (NR-10) - eu posso registrar a ocorrência "
    "para o suporte técnico da GoodWe."
)
RESPOSTA_SPEC_AUSENTE = (
    "Essa especificação não consta na base de dados do ChargeOps que eu tenho acesso, então "
    "prefiro não arriscar um número. Para dados técnicos do equipamento, consulte o manual "
    "do carregador ou o suporte técnico da GoodWe. Posso ajudar com potência das sessões "
    "registradas, consumo, custo e status das estações."
)
RESPOSTA_VAZAMENTO = RECUSA_INJECAO

_EMERGENCIA = re.compile(
    r"\b(choque|levei choque|faisca\w*|fumaca|fumacando|cheiro de queimado|queimando|"
    r"pegando fogo|pegou fogo|incendi\w+|explod\w+|superaquec\w+|derret\w+|estourou)\b"
)
_ELETRICA_DIY = re.compile(
    r"\b(posso|como|quero|vou|devo|da pra|pode eu|tem como eu|eu mesmo|eu proprio)\b.{0,45}"
    r"\b(abrir|mexer|consertar|arrumar|trocar|religar|desmontar|emendar|reparar|desativar|bypass|puxar|instalar|ligar direto|resetar)\b.{0,45}"
    r"\b(carregador|fiacao|fios?|cabos?|disjuntor|dr|quadro|aterramento|tomada|eletroposto|circuito|estacao|chr-?\d+)\b"
)
_JURIDICO = re.compile(
    r"\b(processar|processo judicial|acao judicial|advogad\w*|justica|tribunal|indeniza\w+|"
    r"liminar|procon|notificacao extrajudicial|ilegal|legalidade|juridic\w+|codigo civil|"
    r"clausula|convencao do condominio|me proteger legalmente|direito[s]? (do|de) (consumidor|morador|condomino)|"
    r"posso ser (multado|processado)|cobranca abusiva)\b"
)
_FINANCEIRO = re.compile(
    r"\b(investi\w+|acoes d[aeo]|bolsa de valores|criptomoeda\w*|bitcoin|financiamento|emprestimo|"
    r"vale a pena (comprar|investir|financiar|parcelar|instalar)|retorno (do )?investimento|\broi\b|payback|"
    r"imposto de renda|deduc\w+ fiscal|renegociar (a )?divida|cartao de credito|poupanca|aplicar (meu|o) dinheiro)\b"
)


def moderar_entrada(texto):
    norm = normalizar(texto)
    if _EMERGENCIA.search(norm):
        return ResultadoGuardrail(
            False, "emergencia_eletrica", "relato de risco imediato", RECUSA_EMERGENCIA
        )
    if _ELETRICA_DIY.search(norm):
        return ResultadoGuardrail(
            False, "seguranca_eletrica", "pedido de intervenção elétrica", RECUSA_ELETRICA
        )
    if _JURIDICO.search(norm):
        return ResultadoGuardrail(
            False, "aconselhamento_juridico", "pergunta jurídica", RECUSA_JURIDICA
        )
    if _FINANCEIRO.search(norm):
        return ResultadoGuardrail(
            False, "aconselhamento_financeiro", "pergunta financeira", RECUSA_FINANCEIRA
        )
    return ResultadoGuardrail(True)


_ALLOWLIST_TEXTOS = (RECUSA_FORA_ESCOPO, RECUSA_INJECAO)
_TAM_SHINGLE = 10


def _shingles(texto, n=_TAM_SHINGLE):
    palavras = re.findall(r"\w+", normalizar(texto))
    return {tuple(palavras[i : i + n]) for i in range(max(0, len(palavras) - n + 1))}


def vazou_prompt(saida, prompt):
    permitidos = set()
    for t in _ALLOWLIST_TEXTOS:
        permitidos |= _shingles(t)
    return bool((_shingles(saida) & _shingles(prompt)) - permitidos)


_RE_SPEC_UNIDADE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kva|kw|amperes?|volts?)\b", re.IGNORECASE)
_RE_MODELO = re.compile(r"\b(?:HCA|HCH|GW|GWE|ET|EM)[\s-]?\d{1,4}\w*\b")


def especificacoes_inventadas(saida, base_textos, pergunta=""):
    base = normalizar(" ".join(base_textos) + " " + pergunta)
    base_nums = {n.replace(",", ".") for n, _ in _RE_SPEC_UNIDADE.findall(base)}
    base_nums |= {
        m.replace(",", ".") for m in re.findall(r'"kw":\s*(\d+(?:\.\d+)?)', " ".join(base_textos))
    }
    achadas = []
    for numero, unidade in _RE_SPEC_UNIDADE.findall(saida):
        n = numero.replace(",", ".")
        equivalentes = {n, n.rstrip("0").rstrip("."), f"{float(n):.1f}"}
        if not (equivalentes & base_nums):
            achadas.append(f"{numero} {unidade}")
    for modelo in _RE_MODELO.findall(saida):
        if normalizar(modelo) not in base:
            achadas.append(modelo)
    return achadas


def moderar_saida(saida, prompt, base_textos, pergunta=""):
    if vazou_prompt(saida, prompt):
        return ResultadoGuardrail(
            False, "vazamento_prompt", "saída copia o system prompt", RESPOSTA_VAZAMENTO
        )
    specs = especificacoes_inventadas(saida, base_textos, pergunta)
    if specs:
        return ResultadoGuardrail(
            False, "spec_inventada", f"especificações fora da base: {specs}", RESPOSTA_SPEC_AUSENTE
        )
    return ResultadoGuardrail(True)
