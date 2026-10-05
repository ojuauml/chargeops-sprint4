import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

RE_SECAO = re.compile(r"^\d+\.\s+.+$", re.MULTILINE)
RE_PERGUNTA = re.compile(r"^\d+\.\s+.+\?\s*$", re.MULTILINE)


def _secoes_da_pagina(texto):
    marcas = [(m.start(), m.group().strip()) for m in RE_SECAO.finditer(texto)]
    if not marcas:
        marcas = [(m.start(), m.group().strip()) for m in RE_PERGUNTA.finditer(texto)]
    return marcas


def _secao_do_chunk(marcas, inicio):
    secao = ""
    for offset, titulo in marcas:
        if offset <= inicio:
            secao = titulo
        else:
            break
    return secao


def dividir(documentos, chunk_size, chunk_overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks = []
    for doc in documentos:
        marcas = _secoes_da_pagina(doc.page_content)
        pedacos = splitter.split_documents([doc])
        for pedaco in pedacos:
            inicio = pedaco.metadata.get("start_index", 0)
            secao = _secao_do_chunk(marcas, inicio) or "introdução"
            pedaco.metadata = {
                "fonte": pedaco.metadata["fonte"],
                "fonte_titulo": pedaco.metadata["fonte_titulo"],
                "pagina": pedaco.metadata["pagina"],
                "secao": secao,
            }
            chunks.append(pedaco)
    return chunks
