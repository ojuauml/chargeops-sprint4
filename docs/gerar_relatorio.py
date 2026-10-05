import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    CondPageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parent.parent
ARQ_RESULTADOS = RAIZ / "evals" / "rag_results.json"
ARQ_PDF = RAIZ / "docs" / "relatorio_evolucao.pdf"

GRUPO = "Grupo 6"
TURMA = "1CCR"
ENTREGA = "23/10/2026"
EQUIPE = [
    ("João Lucas", "571355"),
    ("Filipe Gunther", "571131"),
    ("Guilherme Guimaraes", "572957"),
    ("Enzo de Freitas", "572037"),
    ("David Gabriel", "574147"),
    ("Lucas Pinheiro", "573497"),
]

VERDE = colors.HexColor("#0b6b3a")
CINZA = colors.HexColor("#f0f2f1")

estilos = getSampleStyleSheet()
corpo = ParagraphStyle("corpo", parent=estilos["Normal"], fontSize=9.5, leading=13)
celula = ParagraphStyle("celula", parent=corpo, fontSize=8.2, leading=10.2)
celula_cab = ParagraphStyle(
    "celula_cab", parent=celula, fontName="Helvetica-Bold", textColor=colors.white
)
titulo = ParagraphStyle("titulo", parent=estilos["Heading1"], fontSize=16, textColor=VERDE)
sub = ParagraphStyle("sub", parent=estilos["Heading2"], fontSize=11, textColor=VERDE, spaceBefore=8)
pequeno = ParagraphStyle("pequeno", parent=corpo, fontSize=8, leading=10.5)
item = ParagraphStyle("item", parent=corpo, leftIndent=10)


def f(x, casas=2):
    if x is None:
        return "-"
    return f"{x:.{casas}f}".replace(".", ",")


def pct(x):
    if x is None:
        return "-"
    return f"{100 * x:.0f}%"


def tabela(linhas, larguras):
    dados = []
    for i, linha in enumerate(linhas):
        estilo = celula_cab if i == 0 else celula
        dados.append([Paragraph(str(c), estilo) for c in linha])
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo_t = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9cfcc")),
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
    ]
    for i in range(2, len(linhas), 2):
        estilo_t.append(("BACKGROUND", (0, i), (-1, i), CINZA))
    t.setStyle(TableStyle(estilo_t))
    return t


def main():
    if not ARQ_RESULTADOS.exists():
        sys.exit("Falta o evals/rag_results.json. Rode antes: python -m evals.executar_rag")

    dados = json.loads(ARQ_RESULTADOS.read_text(encoding="utf-8"))
    iteracoes = dados.get("iteracoes", {})
    v1, v2 = iteracoes.get("v1"), iteracoes.get("v2")
    if not v1 or not v2:
        sys.exit(
            "O rag_results.json precisa ter as iterações v1 e v2. Rode o eval completo de novo."
        )
    r1, r2 = v1["resumo"], v2["resumo"]

    p = []
    p.append(Paragraph("Relatório de Evolução - Sprint 04", titulo))
    p.append(
        Paragraph(
            f"ChargeOps Assistant - EV Challenge FIAP e GoodWe - {GRUPO} - Turma {TURMA} - Entrega {ENTREGA}",
            pequeno,
        )
    )

    p.append(Paragraph("1. Resumo da evolução", sub))
    p.append(
        Paragraph(
            "Nas Sprints 1 e 2 o chatbot respondia com dados fixos escritos direto no código, sem "
            "buscar nada em nenhum lugar: tudo que ele sabia estava hardcoded. Na Sprint 03 o projeto "
            "virou uma chain em LangChain, com memória de conversa e guardrails, mas ainda sem RAG, "
            "os dados continuavam fixos no código. Na Sprint 04 o projeto ganhou RAG de verdade: os "
            "documentos do condomínio (manual do carregador, regimento, tabela de tarifas e FAQ) foram "
            "colocados em PDF, divididos em pedaços, transformados em vetores com o nomic-embed-text e "
            "guardados num banco Chroma persistente. Agora a resposta vem da busca nesses documentos, "
            "com a fonte citada, e tem uma interface web feita em Gradio para conversar com o "
            "assistente.",
            corpo,
        )
    )

    p.append(CondPageBreak(9 * cm))
    p.append(Paragraph("2. Pipeline RAG", sub))
    p.append(
        Paragraph(
            "A base de conhecimento tem 4 PDFs: o manual do carregador ChargeGrid, o regimento de "
            "recarga compartilhada, a tabela de tarifas e taxas e as perguntas frequentes. Os PDFs são "
            "lidos com PyMuPDFLoader e divididos em pedaços com RecursiveCharacterTextSplitter.",
            corpo,
        )
    )
    p.append(
        Paragraph(
            f"A primeira tentativa de divisão usava pedaços pequenos (chunk_size {r1['chunk_size']}) e "
            f"sem sobreposição, o que fragmentava demais as seções e às vezes cortava uma frase ou um "
            f"valor no meio. A segunda tentativa usa pedaços maiores (chunk_size {r2['chunk_size']}) "
            f"com sobreposição de {r2['chunk_overlap']} caracteres, o que mantém cada seção mais "
            f"inteira. O k (quantidade de pedaços buscados por pergunta) também subiu de {r1['k']} "
            f"para {r2['k']}, trazendo mais contexto.",
            corpo,
        )
    )
    p.append(
        Paragraph(
            "O prompt também mudou entre as duas versões: a primeira só pedia para responder com base "
            "no contexto, sem regra de citação nem de recusa. A segunda exige citar a fonte em todo "
            "texto, recusar pergunta fora do contexto, nunca inventar número e tratar o conteúdo "
            "recuperado como dado, nunca como instrução, mesmo que o documento tenha algo parecido com "
            "um comando escondido.",
            corpo,
        )
    )

    p.append(CondPageBreak(11 * cm))
    p.append(Paragraph("3. Comparativo antes e depois", sub))
    linhas = [
        ["Métrica", "Sprints 1/2 (versão original)", "Sprint 04 (RAG avaliado)"],
        [
            "Busca semântica / RAG",
            "Não existia, dados fixos no código",
            "Sim, ChromaDB + nomic-embed-text",
        ],
        [
            "Nota média no eval (0 a 10)",
            "Não aplicável, sem eval de RAG",
            f"{f(r2['nota_media'])} (iteração 2)",
        ],
        [
            "Faithfulness médio (RAGAS ou fallback)",
            "Não aplicável",
            f"{f(r2['faithfulness_media'])}",
        ],
        [
            "Answer relevancy médio (RAGAS ou fallback)",
            "Não aplicável",
            f"{f(r2['answer_relevancy_media'])}",
        ],
        [
            "Citação de fonte nas respostas",
            "Nunca citava fonte",
            f"{pct(r2['fracao_com_citacao'])} das respostas",
        ],
        [
            "Qualidade do contexto recuperado",
            "Não buscava contexto nenhum",
            f"{r2['k']} trechos por pergunta, chunk de {r2['chunk_size']} caracteres",
        ],
        [
            "Recusa de pergunta fora do contexto",
            "Não tinha essa regra",
            "Sim, por limiar de relevância antes de chamar o modelo",
        ],
        [
            "Proteção contra instrução escondida em documento",
            "Não existia",
            "Sim, filtro de linha suspeita antes de montar o contexto",
        ],
        ["Interface", "Só terminal", "Interface web em Gradio"],
    ]
    p.append(tabela(linhas, [5.4 * cm, 5.8 * cm, 5.8 * cm]))

    p.append(Spacer(1, 8))
    p.append(Paragraph("Scores por iteração", sub))
    linhas_it = [
        [
            "Iteração",
            "chunk_size / overlap",
            "k",
            "Nota eval (0 a 10)",
            "Faithfulness",
            "Answer relevancy",
            "Com citação",
        ],
        [
            "1 (ingênua)",
            f"{r1['chunk_size']} / {r1['chunk_overlap']}",
            str(r1["k"]),
            f(r1["nota_media"]),
            f(r1["faithfulness_media"]),
            f(r1["answer_relevancy_media"]),
            pct(r1["fracao_com_citacao"]),
        ],
        [
            "2 (grounding + citação)",
            f"{r2['chunk_size']} / {r2['chunk_overlap']}",
            str(r2["k"]),
            f(r2["nota_media"]),
            f(r2["faithfulness_media"]),
            f(r2["answer_relevancy_media"]),
            pct(r2["fracao_com_citacao"]),
        ],
    ]
    p.append(
        tabela(linhas_it, [3.4 * cm, 3.0 * cm, 1.2 * cm, 2.4 * cm, 2.2 * cm, 2.6 * cm, 2.2 * cm])
    )
    p.append(
        Paragraph(
            "Mais detalhe sobre cada caso de teste e sobre como as métricas foram calculadas está em "
            "docs/relatorio_rag.md. A comparação entre modelos de geração (temperature, top_p, "
            "max_tokens e k documentados) está em docs/relatorio_modelos.md.",
            pequeno,
        )
    )

    p.append(CondPageBreak(9 * cm))
    p.append(Paragraph("4. Problemas encontrados e soluções", sub))
    problemas = [
        ["Problema", "Causa", "Solução"],
        [
            "O RAGAS não importava (ModuleNotFoundError).",
            "A versão instalada do ragas tenta carregar langchain_community.chat_models.vertexai."
            "ChatVertexAI, que não existe mais nessa versão do langchain-community. Aconteceu com a "
            "0.4.3 e com a 0.2.15.",
            "Usamos o fallback manual documentado que o próprio enunciado permite: faithfulness "
            "checando números e códigos contra o contexto recuperado, e answer relevancy por "
            "similaridade de cosseno entre pergunta e resposta.",
        ],
        [
            "Pedaços pequenos (iteração 1) fragmentavam demais as seções.",
            "Chunk de 300 caracteres sem sobreposição corta uma tabela ou uma frase bem no meio, "
            "perdendo parte da informação.",
            "Aumentar o chunk para 900 caracteres com 150 de sobreposição, mantendo cada seção mais "
            "inteira dentro de um único pedaço.",
        ],
        [
            "Um documento poderia conter um texto parecido com uma instrução escondida.",
            "Se alguém colocasse algo como 'ignore as instruções anteriores' dentro de um PDF da base, "
            "o modelo poderia tentar seguir aquilo como se fosse um comando.",
            "Um filtro roda antes de montar o contexto: troca só a linha suspeita por um aviso, sem "
            "apagar o resto do trecho, e o prompt também reforça que o conteúdo do contexto é dado, "
            "nunca instrução.",
        ],
    ]
    p.append(tabela(problemas, [5.0 * cm, 5.8 * cm, 6.2 * cm]))

    p.append(CondPageBreak(6 * cm))
    p.append(Paragraph("5. Equipe", sub))
    linhas_eq = [["Integrante", "RM"]]
    for nome, rm in EQUIPE:
        linhas_eq.append([nome, rm])
    p.append(tabela(linhas_eq, [10 * cm, 4 * cm]))

    def rodape(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.7 * cm, 1 * cm, f"ChargeOps Assistant - Sprint 04 - {GRUPO}")
        canvas.drawRightString(A4[0] - 1.7 * cm, 1 * cm, f"Página {doc.page}")

    doc = SimpleDocTemplate(
        str(ARQ_PDF),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.6 * cm,
        title="Relatório de Evolução - Sprint 04",
        author=GRUPO,
    )
    doc.build(p, onFirstPage=rodape, onLaterPages=rodape)

    try:
        from pypdf import PdfReader

        paginas = len(PdfReader(str(ARQ_PDF)).pages)
        print("PDF gerado em docs/relatorio_evolucao.pdf com", paginas, "páginas")
        if paginas > 5:
            print("Passou de 5 páginas, o enunciado limita em 5")
    except ImportError:
        print("PDF gerado em docs/relatorio_evolucao.pdf")


if __name__ == "__main__":
    main()
