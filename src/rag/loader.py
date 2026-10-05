from langchain_community.document_loaders import PyMuPDFLoader

from src import config

NOMES_FONTES = {
    "manual_chargegrid": "Manual do Carregador ChargeGrid",
    "regimento_recarga_compartilhada": "Regimento Interno de Recarga Compartilhada",
    "faq_carregamento": "Perguntas Frequentes de Recarga",
    "tabela_tarifas": "Tabela de Tarifas e Taxas",
}


def nome_bonito(stem):
    return NOMES_FONTES.get(stem, stem)


def carregar_documentos(pasta=None):
    pasta = pasta or config.PASTA_KB
    arquivos = sorted(pasta.glob("*.pdf"))
    if not arquivos:
        raise FileNotFoundError(
            f"nenhum PDF encontrado em {pasta}, rode data/knowledge_base/gerar_pdfs.py primeiro"
        )
    documentos = []
    for caminho in arquivos:
        paginas = PyMuPDFLoader(str(caminho)).load()
        for pagina in paginas:
            pagina.metadata["fonte"] = caminho.stem
            pagina.metadata["fonte_titulo"] = nome_bonito(caminho.stem)
            pagina.metadata["pagina"] = pagina.metadata.get("page", 0) + 1
            documentos.append(pagina)
    return documentos
