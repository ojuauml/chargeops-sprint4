from src import config
from src.rag.chunking import dividir
from src.rag.embeddings import criar_embeddings
from src.rag.loader import carregar_documentos

CONFIG_INDEXACAO = {
    "v1": {"chunk_size": 300, "chunk_overlap": 0, "k": 2},
    "v2": {"chunk_size": 900, "chunk_overlap": 150, "k": 4},
}


def _persist_dir(versao):
    caminho = config.PASTA_CHROMA / versao
    caminho.mkdir(parents=True, exist_ok=True)
    return str(caminho)


def obter_vector_store(versao, embeddings=None):
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=f"chargeops_{versao}",
        embedding_function=embeddings or criar_embeddings(),
        persist_directory=_persist_dir(versao),
        collection_metadata={"hnsw:space": "cosine"},
    )


def indexar(versao, embeddings=None, documentos=None):
    cfg = CONFIG_INDEXACAO[versao]
    documentos = documentos if documentos is not None else carregar_documentos()
    chunks = dividir(documentos, cfg["chunk_size"], cfg["chunk_overlap"])
    store = obter_vector_store(versao, embeddings)
    ids = [f"{d.metadata['fonte']}-p{d.metadata['pagina']}-{i}" for i, d in enumerate(chunks)]
    store.reset_collection()
    store.add_documents(chunks, ids=ids)
    return store, len(chunks)
