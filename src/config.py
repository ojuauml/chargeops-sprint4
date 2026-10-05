import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PROMPTS = RAIZ / "prompts"
PASTA_EVALS = RAIZ / "evals"
PASTA_DOCS = RAIZ / "docs"
PASTA_KB = RAIZ / "data" / "knowledge_base"
PASTA_CHROMA = RAIZ / "data" / "chroma_db"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

MODELO_PRINCIPAL = os.getenv("MODELO_PRINCIPAL", "gpt-oss:120b")
MODELO_SECUNDARIO = os.getenv("MODELO_SECUNDARIO", "qwen3:8b")
MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "nomic-embed-text")

VERSAO_RAG_PADRAO = os.getenv("VERSAO_RAG", "v2")
K_PADRAO = int(os.getenv("RAG_K", "4"))
LIMIAR_GROUNDING = float(os.getenv("RAG_LIMIAR_GROUNDING", "0.2"))

PARAMETROS_PADRAO = {
    "temperature": float(os.getenv("TEMPERATURE", "0.3")),
    "top_p": float(os.getenv("TOP_P", "0.9")),
    "max_tokens": int(os.getenv("MAX_TOKENS", "4096")),
}
OLLAMA_REASONING = os.getenv("OLLAMA_REASONING") or None

LIMITE_TOKENS_MEMORIA = int(os.getenv("LIMITE_TOKENS_MEMORIA", "1500"))
VERSAO_PROMPT_PADRAO = os.getenv("VERSAO_PROMPT", "v3")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODELO = "llama-3.3-70b-versatile"
