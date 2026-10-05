from src import config


def criar_embeddings(modelo=None):
    from langchain_ollama import OllamaEmbeddings

    kwargs = dict(
        model=modelo or config.MODELO_EMBEDDING,
        base_url=config.OLLAMA_BASE_URL,
    )
    if config.OLLAMA_API_KEY:
        kwargs["client_kwargs"] = {"headers": {"Authorization": f"Bearer {config.OLLAMA_API_KEY}"}}
    return OllamaEmbeddings(**kwargs)
