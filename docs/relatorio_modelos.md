# Relatório de uso de modelos e parâmetros - Sprint 04 (RAG)

Comparação feita com o mesmo pipeline RAG (iteração v2, chunk_size 900, overlap 150, k=4) e o mesmo conjunto de perguntas (evals/rag_eval_set.py), trocando só o modelo de geração.

## Parâmetros usados

| Parâmetro | gpt-oss:120b-cloud | qwen3:8b | Motivo |
|---|---|---|---|
| temperature | 0.0 | 0.0 | 0, como recomendado para RAG: a resposta deve vir só do contexto recuperado, sem variação criativa |
| top_p | 0.9 | 0.9 | mantido no padrão do projeto |
| max_tokens | 4096 | 4096 | alto o bastante para a resposta não sair cortada |
| k (trechos buscados) | 4 | 4 | mesmo valor nos dois, para a comparação ser justa |
| modelo de embeddings | nomic-embed-text | nomic-embed-text | mesmo modelo de vetorização para os dois, só o modelo de geração muda |

## Resultados

| Métrica | gpt-oss:120b-cloud | qwen3:8b |
|---|---|---|
| Nota média no eval (0 a 10) | 8,18 | 8,94 |
| Faithfulness médio (0 a 1) | 1,00 | 1,00 |
| Answer relevancy médio (0 a 1) | 0,87 | 0,89 |
| Respostas com citação de fonte | 89% | 100% |
| Tokens de entrada por pergunta | 1204 | 1204 |
| Latência média (s) | 1,54 | 8,99 |

## Observações

- Modelo de embeddings e chunking são os mesmos nos dois casos, então a diferença de resultado vem só da geração.
- As notas vêm das checagens automáticas de evals/avaliador_rag.py mais as métricas de faithfulness e answer relevancy de src/rag/metricas.py.
- Cada configuração rodou uma vez, então pequenas variações entre rodadas são esperadas mesmo com temperature 0.
