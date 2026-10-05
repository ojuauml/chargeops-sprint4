# Relatório da avaliação RAG

Comparação entre as duas iterações de ingestão e prompt, nos mesmos 11 casos de teste (evals/rag_eval_set.py), sobre a mesma base de conhecimento (data/knowledge_base/).

## Decisões de chunking

A iteração 1 usa chunk_size 300 e overlap 0 (chunks pequenos, sem sobreposição): fragmenta demais os parágrafos, então um trecho recuperado às vezes corta uma frase no meio e perde uma parte da informação. A iteração 2 usa chunk_size 900 e overlap 150, que mantém cada seção mais inteira e a sobreposição evita cortar uma frase bem na fronteira entre dois chunks. O k (quantidade de trechos buscados) também mudou de 2 para 4, trazendo mais contexto por pergunta.

O prompt também mudou entre as duas iterações: a v1 só pede para responder com base no contexto, sem regra de citação, sem regra de recusa fora de contexto e sem proteção contra instrução escondida dentro de um documento. A v2 exige citar a fonte, recusar pergunta fora do contexto, nunca inventar número e tratar o conteúdo de <contexto> como dado e não como instrução.

## Scores por iteração

| Métrica | Iteração 1 (ingênua) | Iteração 2 (grounding + citação) |
|---|---|---|
| Nota média no eval (0 a 10) | 3,94 | 8,18 |
| Faithfulness médio (0 a 1) | 1,00 | 1,00 |
| Answer relevancy médio (0 a 1) | 0,88 | 0,87 |
| Respostas com citação de fonte | 0% | 89% |
| Chunks indexados | 27 | 10 |
| Tokens de entrada por pergunta | 249 | 1204 |
| Latência média (s) | 2,45 | 1,39 |

Ganho de nota da iteração 1 para a 2: 4,24 pontos.

## Nota por caso

| Caso | Categoria | Nota v1 | Nota v2 | Faithfulness v1 | Faithfulness v2 |
|---|---|---|---|---|---|
| R1 | manual | 6,67 | 10,00 | 1,00 | 1,00 |
| R2 | manual | 2,50 | 7,50 | 1,00 | 1,00 |
| R3 | regimento | 5,00 | 7,50 | 1,00 | 1,00 |
| R4 | tarifas | 3,33 | 10,00 | 1,00 | 1,00 |
| R5 | regimento | 3,33 | 3,33 | 1,00 | 1,00 |
| R6 | tarifas | 3,33 | 10,00 | 1,00 | 1,00 |
| R7 | faq | 2,50 | 10,00 | 1,00 | 1,00 |
| R8 | cruzado | 6,67 | 10,00 | 1,00 | 1,00 |
| R9 | fora_contexto | 3,33 | 6,67 | 1,00 | 1,00 |
| R10 | fora_contexto | 0,00 | 5,00 | 1,00 | 1,00 |
| R11 | seguranca | 6,67 | 10,00 | 1,00 | 1,00 |

## Como as métricas foram calculadas

RAGAS não funcionou neste ambiente: ao importar, a versão instalada tenta carregar `langchain_community.chat_models.vertexai.ChatVertexAI`, que não existe mais nessa versão do langchain-community (erro `ModuleNotFoundError`). Isso aconteceu com a 0.4.3 e também com a 0.2.15. Por isso usamos o fallback manual documentado, permitido pelo enunciado:

- **faithfulness_manual**: procura números, valores em reais, códigos de erro, kWh e datas dentro da resposta e confere se cada um aparece literalmente nos trechos recuperados. Se a resposta não tem nenhum número ou código para checar, o score é 1,0 (nada a conferir). É equivalente ao faithfulness do RAGAS porque mede a mesma coisa: se a resposta está apoiada no contexto, só que de forma determinística em vez de usar um LLM juiz.
- **answer_relevancy_manual**: similaridade de cosseno entre o embedding da pergunta e o embedding da resposta, usando o mesmo modelo de embeddings da vetorização (nomic-embed-text). É a mesma ideia do answer_relevancy do RAGAS (que compara pergunta e resposta por embedding), simplificada para não precisar gerar perguntas reversas com um LLM. Se os embeddings não estiverem disponíveis, cai para sobreposição de palavras entre pergunta e resposta.
- Essas duas métricas e a citação de fonte são calculadas por `src/rag/metricas.py`, chamado automaticamente dentro de `RagAssistant.perguntar`.
