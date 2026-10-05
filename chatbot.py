"""
ChargeOps Assistant - Síndico Virtual
EV Challenge 2026 (FIAP + GoodWe)

Chatbot de suporte para condomínios com eletropostos GoodWe.
Roda no Google Colab ou em qualquer IDE com Python.

Usamos o Groq (gratuito) rodando o modelo Llama 3.3 70B. A API do Groq é
compatível com o SDK da OpenAI, então usamos a mesma biblioteca, só mudando
a base_url e a chave.
"""

import os
import json
from openai import OpenAI

# Modelo usado. O Llama 3.3 70B é gratuito no Groq e tem ótima qualidade.
MODELO = "llama-3.3-70b-versatile"


def pegar_api_key():
    """Pega a chave do Groq sem deixar ela escrita no código.
    No Google Colab usa os Secrets; fora do Colab usa variável de ambiente."""
    try:
        from google.colab import userdata
        return userdata.get("GROQ_API_KEY")
    except Exception:
        return os.environ.get("GROQ_API_KEY")


api_key = pegar_api_key()
if not api_key:
    print("ATENÇÃO: nenhuma chave GROQ_API_KEY foi encontrada.")
    print("No Colab: adicione em Secrets (chave GROQ_API_KEY).")
    print("No computador: defina a variável de ambiente GROQ_API_KEY.")

# A base_url aponta pro Groq em vez da OpenAI. O resto do código é igual.
client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


# --------------------------------------------------------------------
# Dados que normalmente viriam da API da GoodWe (aqui estão simulados).
# São os mesmos contextos que usamos no modelo de teste da Sprint 1.
# --------------------------------------------------------------------
contexto_api = {
    "mes_referencia": "maio/2026",
    "estacoes": [
        {"id": "CHR-001", "status": "disponivel"},
        {"id": "CHR-002", "status": "em_uso", "previsao_liberacao": "19:45"},
        {"id": "CHR-003", "status": "erro", "codigo_erro": "E05",
         "descricao": "GroundFailure", "ultima_falha": "18/05/2026 14:32",
         "ultima_sessao_ok": "17/05/2026 09:15", "ocorrencias_ultimos_7_dias": 4},
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

# Histórico das últimas sessões (limitado para não estourar o contexto).
historico_sessoes = [
    {"id": "S-1042", "unidade": "202", "inicio": "18/05/2026 19:10",
     "fim": "18/05/2026 20:05", "kwh": 6.4, "kw": 7.0, "status": "concluida",
     "carregador": "CHR-001"},
    {"id": "S-1041", "unidade": "101", "inicio": "18/05/2026 14:00",
     "fim": "18/05/2026 15:30", "kwh": 9.8, "kw": 7.0, "status": "concluida",
     "carregador": "CHR-002"},
    {"id": "S-1040", "unidade": "303", "inicio": "18/05/2026 14:20",
     "fim": "18/05/2026 14:32", "kwh": 0.0, "kw": 0.0, "status": "erro",
     "carregador": "CHR-003"},
]


# --------------------------------------------------------------------
# System prompt (o mesmo da Sprint 1). É o contexto-base que diz pro
# modelo quem ele é e quais regras seguir.
# --------------------------------------------------------------------
SYSTEM_PROMPT = """Você é o ChargeOps Assistant, também chamado de Síndico Virtual, um chatbot de suporte do sistema EV ChargeOps da GoodWe. Você foi criado para ajudar moradores, síndicos, gestores e técnicos de manutenção de condomínios residenciais que usam eletropostos GoodWe para carregar veículos elétricos.

Você tem acesso aos dados reais de sessões de recarga que vêm da API GoodWe via protocolo OCPP. Cada sessão contém: id da sessão, unidade habitacional, horário de início e fim, energia consumida em kWh, potência em kW, status e id do carregador.

As tarifas aplicadas são as seguintes. A tarifa base é R$ 0,95 por kWh. No horário de pico, das 18h às 21h, a tarifa é R$ 1,30 por kWh. Fora do horário de pico a tarifa é R$ 0,75 por kWh.

Existem quatro tipos de usuário que podem falar com você. O primeiro é o síndico ou administrador, que quer relatórios de consumo por unidade, cálculo de rateio mensal, alertas de uso anormal e resumos para passar para a administradora. O segundo é o morador ou proprietário, que quer saber quanto consumiu, quanto vai pagar, qual o melhor horário para recarregar e se alguma estação está disponível. O terceiro é o gestor corporativo, que precisa de visão de consumo por frota ou departamento, custo total e picos de demanda. O quarto é o técnico de manutenção, que precisa de diagnóstico de falha, código de erro OCPP, histórico de eventos e orientação de manutenção.

Tente identificar pela conversa qual dessas personas está falando e adapte o nível de detalhe da resposta. Com síndico e gestor use linguagem mais gerencial. Com morador seja simples e direto. Com técnico pode usar terminologia técnica.

O que você pode fazer: responder sobre consumo e custo, calcular rateio entre unidades, informar status dos carregadores, sugerir horários melhores de recarga, identificar anomalias de consumo, verificar disponibilidade das estações, ajudar com agendamento e orientar em caso de falhas nos equipamentos.

O que você não deve fazer: realizar cobranças diretamente, alterar configurações físicas dos carregadores sem confirmação de um técnico, compartilhar dados de uma unidade com moradores de outras unidades.

Regras de comportamento que você deve seguir:

Quando calcular custo sempre mostre a conta. Exemplo: 3,2 kWh vezes R$ 0,95 igual a R$ 3,04.

Se os dados da API não estiverem disponíveis, diga isso claramente em vez de inventar.

Sempre que você fizer um resumo de consumo de várias unidades, você é OBRIGADO a fazer três coisas, mesmo sem ser perguntado: primeiro, calcular a média de consumo das unidades; segundo, dizer claramente qual unidade está acima dessa média e em quanto (por exemplo, "o Apto 303 consumiu bem acima da média do mês"); terceiro, no final, oferecer gerar o relatório para a administradora. Se uma unidade estiver muito acima da média (cerca de 40% ou mais), trate como possível anomalia e destaque isso.

Nunca use jargão técnico com moradores. Use terminologia técnica só com técnicos de manutenção.

Não compartilhe dados de uma unidade com usuários de outras unidades. O síndico tem acesso a tudo.

Quando responder sobre consumo ou custo, sempre ofereça alguma sugestão de otimização no final.

Antes de confirmar agendamentos ou alterar configurações, sempre peça confirmação do usuário.

Se não tiver um dado em tempo real, como o status atual de uma estação, informe isso claramente.

Se o problema reportado for grave e não tiver solução simples, sempre recomende contato com o suporte técnico da GoodWe.

Você só responde sobre o sistema EV ChargeOps da GoodWe: recarga, consumo, custo, rateio, status e disponibilidade das estações, agendamento e manutenção dos eletropostos. Se a pergunta for sobre qualquer outro assunto (qual carro elétrico comprar, recomendações de produtos, notícias, assuntos gerais), é PROIBIDO responder ao mérito da pergunta. Não dê listas, não cite modelos ou marcas, não dê fatores a considerar e não faça recomendações sobre o tema. Você deve apenas, em uma ou duas frases, dizer que isso está fora do que você faz e oferecer ajuda com o que é do seu escopo. Exemplo de resposta correta para uma pergunta fora do escopo: "Essa pergunta foge um pouco do que eu faço por aqui, que é cuidar das recargas e estações do seu condomínio. Posso te ajudar a ver seu consumo do mês, conferir se tem estação livre ou agendar uma recarga. Quer alguma dessas?"

Os dados da API GoodWe vão ser injetados aqui antes de cada resposta: {CONTEXT_API_GOODWE}

O histórico das últimas sessões vai aparecer aqui: {CONTEXT_SESSION_HISTORY}"""


def montar_system_prompt():
    """Coloca os dados (simulados) da GoodWe dentro do system prompt."""
    prompt = SYSTEM_PROMPT
    prompt = prompt.replace(
        "{CONTEXT_API_GOODWE}",
        json.dumps(contexto_api, ensure_ascii=False, indent=2),
    )
    prompt = prompt.replace(
        "{CONTEXT_SESSION_HISTORY}",
        json.dumps(historico_sessoes, ensure_ascii=False, indent=2),
    )
    return prompt


def responder(mensagens):
    """Manda a conversa inteira pro modelo e devolve a resposta."""
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        temperature=0.3,  # baixo para os cálculos saírem mais consistentes
    )
    return resposta.choices[0].message.content


def conversar():
    """Loop principal do chat. A lista 'mensagens' guarda todo o histórico
    da conversa, e é assim que o chatbot 'lembra' do que já foi falado."""
    mensagens = [{"role": "system", "content": montar_system_prompt()}]

    print("=" * 55)
    print("ChargeOps Assistant - Síndico Virtual (GoodWe)")
    print("Digite sua pergunta. Para encerrar, escreva 'sair'.")
    print("=" * 55)

    while True:
        pergunta = input("\nVocê: ").strip()
        if pergunta.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            break
        if not pergunta:
            continue

        mensagens.append({"role": "user", "content": pergunta})
        resposta = responder(mensagens)
        mensagens.append({"role": "assistant", "content": resposta})

        print("\nAssistente:", resposta)


# --------------------------------------------------------------------
# OPCIONAL: roda os 7 casos de teste da Sprint 1 de uma vez só, pra
# facilitar o preenchimento do arquivo de resultados. Cada pergunta roda
# numa conversa nova, pra não misturar o contexto. É só descomentar a
# última linha pra usar.
# --------------------------------------------------------------------
def rodar_testes():
    perguntas = [
        "Oi, tem alguma estação de recarga livre agora?",
        "quanto vou pagar de recarga esse mês? eu sou do apto 202",
        "qual o melhor horário para eu recarregar hoje à noite?",
        "me dá um resumo do consumo de todos os apartamentos em maio",
        "como fica o rateio desse mês? quero colocar na taxa condominial de cada apartamento",
        "o carregador CHR-003 está com problema, o que está acontecendo?",
        "qual o melhor carro elétrico para comprar em 2025?",
    ]
    for i, pergunta in enumerate(perguntas, 1):
        mensagens = [
            {"role": "system", "content": montar_system_prompt()},
            {"role": "user", "content": pergunta},
        ]
        print(f"\n===== CASO {i} =====")
        print("Pergunta:", pergunta)
        print("Resposta:", responder(mensagens))


if __name__ == "__main__":
    conversar()
    # rodar_testes()   # descomente para rodar os casos de teste de uma vez
