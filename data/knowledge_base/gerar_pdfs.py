from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

PASTA = Path(__file__).resolve().parent

estilos = getSampleStyleSheet()
titulo = ParagraphStyle("titulo", parent=estilos["Title"], fontSize=16)
h1 = ParagraphStyle("h1", parent=estilos["Heading1"], fontSize=13, spaceBefore=10)
h2 = ParagraphStyle("h2", parent=estilos["Heading2"], fontSize=11, spaceBefore=8)
corpo = ParagraphStyle("corpo", parent=estilos["Normal"], fontSize=10, leading=14)
pergunta = ParagraphStyle("pergunta", parent=corpo, fontName="Helvetica-Bold")


def tabela(linhas, larguras):
    t = Table(linhas, colWidths=larguras)
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def gerar(nome, elementos):
    doc = SimpleDocTemplate(
        str(PASTA / nome),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(elementos)
    print("gerado", nome)


def manual_chargegrid():
    e = [
        Paragraph("Manual do Carregador GoodWe ChargeGrid - linha EV ChargeOps", titulo),
        Spacer(1, 12),
    ]

    e.append(Paragraph("1. Visao geral", h1))
    e.append(
        Paragraph(
            "O ChargeGrid Home 7.4 e o carregador AC monofasico instalado nas quatro estacoes do "
            "condominio (CHR-001, CHR-002, CHR-003 e CHR-004). Potencia nominal de 7,4 kW, conector "
            "tipo 2, grau de protecao IP55 (uso em area coberta ou externa). As sessoes registradas no "
            "sistema costumam ficar perto de 7,0 kW porque o carregador ajusta a potencia conforme a "
            "bateria do veiculo.",
            corpo,
        )
    )

    e.append(Paragraph("2. Instalacao", h1))
    e.append(
        Paragraph(
            "Cada carregador exige circuito eletrico dedicado, disjuntor termomagnetico de 32A e "
            "dispositivo DR tipo A de 30mA. O aterramento e obrigatorio e monitorado pelo proprio "
            "equipamento: se a continuidade do condutor PE falhar, o carregador bloqueia a recarga e "
            "mostra o erro E05. A instalacao so pode ser feita por eletricista ou engenheiro "
            "eletricista habilitado (NR-10).",
            corpo,
        )
    )

    e.append(Paragraph("3. Sinalizacao por LED", h1))
    e.append(
        tabela(
            [
                ["Indicacao", "Significado"],
                ["LED verde fixo", "Carregador disponivel"],
                ["LED azul piscando", "Sessao de recarga em andamento"],
                ["LED vermelho fixo", "Erro, veja a tabela de codigos na secao 4"],
                ["LED apagado", "Carregador sem energia ou desligado no quadro"],
            ],
            [8 * cm, 8 * cm],
        )
    )

    e.append(Spacer(1, 10))
    e.append(Paragraph("4. Codigos de erro", h1))
    e.append(
        tabela(
            [
                ["Codigo", "Nome", "Descricao"],
                ["E01", "Sobrecorrente", "Corrente acima do suportado pelo circuito"],
                ["E02", "Subtensao", "Tensao da rede abaixo do minimo de operacao"],
                ["E03", "Sobretemperatura", "Temperatura interna do carregador acima do limite"],
                [
                    "E04",
                    "Falha de comunicacao OCPP",
                    "Carregador perdeu conexao com o sistema central",
                ],
                [
                    "E05",
                    "GroundFailure",
                    "Falha de aterramento ou corrente de fuga para a terra. Exige isolar o circuito, "
                    "medir a continuidade do condutor PE e verificar o DR. Procedimento somente para "
                    "profissional habilitado (NR-10), risco de choque eletrico. Se persistir, abrir "
                    "chamado no suporte tecnico da GoodWe.",
                ],
                ["E06", "Cabo mal conectado", "O conector tipo 2 nao foi encaixado corretamente"],
                ["E07", "Bloqueio por agendamento", "Horario reservado por outra unidade"],
                ["E08", "Firmware desatualizado", "Atualizacao de firmware pendente"],
            ],
            [2 * cm, 5 * cm, 9 * cm],
        )
    )

    e.append(Spacer(1, 10))
    e.append(Paragraph("5. Manutencao preventiva", h1))
    e.append(
        Paragraph(
            "Inspecao trimestral feita por tecnico habilitado, revisao anual do aterramento e limpeza "
            "do conector a cada seis meses. O morador nunca deve abrir o carregador ou mexer na "
            "fiacao, mesmo para limpeza.",
            corpo,
        )
    )

    e.append(Paragraph("6. Garantia", h1))
    e.append(
        Paragraph(
            "Garantia de 5 anos para o carregador e 2 anos para o cabo. A garantia nao cobre danos "
            "causados por instalacao fora das normas ou por intervencao de pessoa nao habilitada.",
            corpo,
        )
    )

    gerar("manual_chargegrid.pdf", e)


def regimento():
    e = [Paragraph("Regimento Interno de Recarga Compartilhada", titulo), Spacer(1, 12)]

    e.append(Paragraph("1. Finalidade e abrangencia", h1))
    e.append(
        Paragraph(
            "Este regimento regula o uso das quatro estacoes de recarga do condominio (CHR-001 a "
            "CHR-004) por moradores, visitantes e prestadores de servico.",
            corpo,
        )
    )

    e.append(Paragraph("2. Regras de uso", h1))
    e.append(
        Paragraph(
            "Cada sessao de recarga pode durar no maximo 4 horas corridas por veiculo. E proibido "
            "desconectar o veiculo de outro morador sem autorizacao da portaria. A fila de espera e "
            "controlada pelo aplicativo do condominio.",
            corpo,
        )
    )

    e.append(Paragraph("3. Prioridades", h1))
    e.append(
        Paragraph(
            "Moradores com veiculo eletrico cadastrado tem prioridade sobre visitantes. O sindico pode "
            "reservar uma estacao para manutencao programada, avisando com 48 horas de antecedencia.",
            corpo,
        )
    )

    e.append(Paragraph("4. Agendamento", h1))
    e.append(
        Paragraph(
            "O agendamento pode ser feito com ate 24 horas de antecedencia. Se o morador nao iniciar a "
            "recarga em ate 15 minutos do horario marcado, a reserva e cancelada automaticamente e a "
            "estacao libera para o proximo da fila.",
            corpo,
        )
    )

    e.append(Paragraph("5. Rateio de custos", h1))
    e.append(
        Paragraph(
            "A taxa de infraestrutura mensal de R$ 80,00 e dividida igualmente entre as unidades "
            "cadastradas nos carregadores. O consumo de energia e cobrado a parte, conforme a tarifa "
            "vigente no horario da recarga: R$ 0,75 por kWh fora de pico (21h as 24h), R$ 0,95 por kWh "
            "em horario normal (00h as 18h) e R$ 1,30 por kWh no horario de pico (18h as 21h). A tabela "
            "completa de tarifas esta no documento de tarifas.",
            corpo,
        )
    )

    e.append(Paragraph("6. Penalidades", h1))
    e.append(
        Paragraph(
            "O uso alem do limite de 4 horas gera multa de R$ 15,00 por hora excedente, revertida ao "
            "fundo de manutencao dos carregadores. A reincidencia em 3 meses leva a suspensao do "
            "cadastro por 30 dias.",
            corpo,
        )
    )

    e.append(Paragraph("7. Alteracoes do regimento", h1))
    e.append(
        Paragraph(
            "Mudancas neste regimento sao aprovadas em assembleia e as atas ficam arquivadas com a "
            "administradora do condominio.",
            corpo,
        )
    )

    gerar("regimento_recarga_compartilhada.pdf", e)


def faq():
    e = [Paragraph("Perguntas Frequentes - Recarga de Veiculos Eletricos", titulo), Spacer(1, 12)]

    perguntas = [
        (
            "Como sei se tem uma estacao livre?",
            "Consulte o aplicativo do condominio ou pergunte ao assistente, que mostra o status das "
            "quatro estacoes (CHR-001 a CHR-004) em tempo real.",
        ),
        (
            "Como funciona a cobranca da recarga?",
            "O valor e a energia consumida (kWh) multiplicada pela tarifa do horario em que a recarga "
            "aconteceu, mais a parte proporcional da taxa de infraestrutura mensal. A tabela de "
            "tarifas e o regimento de recarga compartilhada tem os valores exatos.",
        ),
        (
            "Posso usar a estacao que outro morador reservou?",
            "Nao, sem autorizacao da portaria, conforme o regimento interno de recarga compartilhada.",
        ),
        (
            "O carregador deu um codigo de erro, o que eu faco?",
            "Anote o codigo mostrado (por exemplo E05) e abra um chamado pelo aplicativo ou avise a "
            "portaria. Nunca tente abrir o carregador ou mexer na fiacao sozinho, isso envolve risco "
            "de choque eletrico e so pode ser feito por um profissional habilitado.",
        ),
        (
            "Posso carregar depois da meia-noite?",
            "Pode. A tarifa muda conforme a faixa horaria do dia, veja a tabela de tarifas.",
        ),
        (
            "Quem faz a manutencao dos carregadores?",
            "Um tecnico habilitado contratado pela administradora, ou o suporte tecnico da GoodWe em "
            "casos mais graves.",
        ),
        (
            "Posso instalar um carregador particular na minha vaga?",
            "So com aprovacao em assembleia e um projeto eletrico assinado por um engenheiro "
            "eletricista.",
        ),
        (
            "Existe multa por uso indevido da estacao?",
            "Sim. As multas por sessao excedente e as regras de suspensao de cadastro estao no "
            "regimento interno de recarga compartilhada.",
        ),
        (
            "Da pra saber quanto vou pagar antes de carregar?",
            "Da sim, uma estimativa com base na tarifa do horario escolhido e no consumo medio do seu "
            "veiculo.",
        ),
        (
            "Tenho uma duvida juridica ou financeira sobre a cobranca, quem eu procuro?",
            "O assistente nao da esse tipo de orientacao. Para questoes juridicas procure um advogado, "
            "e para questoes financeiras um contador ou consultor habilitado.",
        ),
    ]
    for i, (p, r) in enumerate(perguntas, 1):
        e.append(Paragraph(f"{i}. {p}", pergunta))
        e.append(Paragraph(r, corpo))
        e.append(Spacer(1, 6))

    gerar("faq_carregamento.pdf", e)


def tarifas():
    e = [Paragraph("Tabela de Tarifas e Taxas - ChargeOps", titulo), Spacer(1, 12)]

    e.append(Paragraph("1. Tarifas por faixa horaria", h1))
    e.append(
        tabela(
            [
                ["Faixa horaria", "Classificacao", "Tarifa (R$/kWh)"],
                ["00h as 17h59", "Normal", "0,95"],
                ["18h as 20h59", "Pico", "1,30"],
                ["21h as 23h59", "Fora de pico", "0,75"],
            ],
            [5 * cm, 5 * cm, 5 * cm],
        )
    )

    e.append(Spacer(1, 10))
    e.append(Paragraph("2. Taxa de infraestrutura", h1))
    e.append(
        Paragraph(
            "Taxa fixa de R$ 80,00 por mes, dividida igualmente entre as unidades cadastradas nos "
            "carregadores, independente de quanto cada uma consumiu.",
            corpo,
        )
    )

    e.append(Paragraph("3. Historico de reajuste", h1))
    e.append(
        Paragraph(
            "A tarifa de pico era R$ 1,10 por kWh ate dezembro de 2025. Em janeiro de 2026, apos "
            "aprovacao em assembleia, passou para R$ 1,30 por kWh para refletir o custo mais alto da "
            "energia nesse horario.",
            corpo,
        )
    )

    e.append(Paragraph("4. Multas", h1))
    e.append(
        Paragraph(
            "Sessao de recarga que ultrapassa o limite de 4 horas corridas gera multa de R$ 15,00 por "
            "hora excedente, conforme o regimento interno de recarga compartilhada.",
            corpo,
        )
    )

    gerar("tabela_tarifas.pdf", e)


if __name__ == "__main__":
    manual_chargegrid()
    regimento()
    faq()
    tarifas()
