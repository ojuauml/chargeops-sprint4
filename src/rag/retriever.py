def buscar(vector_store, pergunta, k=4):
    resultados = vector_store.similarity_search_with_score(pergunta, k=k)
    saida = []
    for documento, distancia in resultados:
        relevancia = max(0.0, 1.0 - distancia)
        saida.append((documento, relevancia))
    saida.sort(key=lambda par: par[1], reverse=True)
    return saida
