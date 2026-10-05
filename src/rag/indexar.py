import argparse

from src.rag.embeddings import criar_embeddings
from src.rag.vector_store import indexar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default="v2", choices=["v1", "v2"])
    args = ap.parse_args()

    embeddings = criar_embeddings()
    _, total = indexar(args.versao, embeddings)
    print(f"indexado {args.versao}: {total} chunks")


if __name__ == "__main__":
    main()
