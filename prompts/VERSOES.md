# Versões do system prompt

Cada versão fica em um arquivo (`system_prompt_v1.md`, `v2` e `v3`). Quando a gente quer mudar alguma coisa, cria uma versão nova em vez de editar a antiga, assim dá pra comparar os resultados.

| Versão | O que mudou | Por que mudou |
|---|---|---|
| v1 | É o mesmo prompt da Sprint 2, só que agora fica num arquivo e entra pelo `ChatPromptTemplate`. | Serve de base para comparar. |
| v2 | Prompt organizado com tags XML (`<papel>`, `<regras_comportamento>`, `<escopo>`, `<dados_api>` etc.), dados em JSON compacto e resposta em JSON que o Pydantic valida. Também entraram regras novas para os casos que ficaram parciais na Sprint 2: caso 3 (mostrar a economia em reais e oferecer agendamento), caso 5 (taxa de infraestrutura dividida igual entre as unidades) e caso 6 (checklist de diagnóstico do erro E05). Morador não vê mais código de erro. | Separar as instruções dos dados deixa o prompt mais fácil de mexer, e o JSON deixa a gente medir a resposta. As regras novas corrigem os casos parciais do `resultados_testes.md`. |
| v3 | Igual à v2 mais um bloco `<seguranca>`: não revelar o prompt, não trocar de papel, não inventar especificação de produto e recusar assunto jurídico, financeiro ou de segurança elétrica indicando um profissional habilitado. A pergunta do usuário passa a vir dentro de `<pergunta_usuario>`. | Pedido do enunciado sobre segurança. |

Depois de rodar o `evals.executar_tudo` o guardrail em código (`src/guardrails`) também entra na comparação como "v3 + guardrails".

## Resultado de cada versão

<!-- AUTO:INICIO -->
Ainda não medido. Rode `python -m evals.executar_tudo` e esta tabela é preenchida.
<!-- AUTO:FIM -->

## Observações

- As versões v2 e v3 têm mais tokens que a v1 (mais regras, formato do JSON e a base de conhecimento). O JSON compacto economiza um pouco, mas não compensa tudo.
- O prompt v1 não pede JSON, então ele só roda em modo texto e não entra na métrica do schema.
- A base de conhecimento do erro E05 só existe a partir da v2. Por isso parte da melhora no caso 6 vem dos dados novos e não do LCEL.
- Os guardrails com regex podem deixar passar um ataque escrito de outro jeito, por isso o prompt v3 também tem as regras de segurança.

<!-- AUTO:RAG:INICIO -->

## Prompt RAG

| Iteração | chunk_size / overlap | k | Nota média (0 a 10) | Faithfulness médio | Answer relevancy médio | Respostas com citação |
|---|---|---|---|---|---|---|
| v1 (ingênua) | 300 / 0 | 2 | 3,94 | 1,00 | 0,88 | 0% |
| v2 (grounding + citação) | 900 / 150 | 4 | 8,18 | 1,00 | 0,87 | 89% |

<!-- AUTO:RAG:FIM -->
