# EV ChargeOps Assistant

Projeto desenvolvido para o EV Challenge 2026, parceria FIAP e GoodWe.

## Integrantes

[João Lucas] - RM: 571355
[Filipe] - RM: 571131
[Guilherme] - RM: 572957
[Enzo] - RM: 572037
[David] - RM: 574147
[Lucas] - RM: 573497

## Sprint 03: refatoração com LangChain

Na Sprint 03 a gente pegou o chatbot da Sprint 2 (o `chatbot.py` continua no repositório como versão antiga, usada para comparar) e reorganizou em pastas usando LangChain LCEL.

| O que o enunciado pede | Onde está |
|---|---|
| Chain LCEL (prompt, llm e parser) com ChatOllama | `src/chain/builder.py` |
| Memória por sessão com limite de tokens | `src/chain/memoria.py` |
| Resposta estruturada com Pydantic v2 | `src/schemas/consulta_recarga.py` |
| Prompt versionado em XML e contagem de tokens (tiktoken) | `prompts/` e `src/chain/tokens.py` |
| Guardrails (jailbreak, escopo, jurídico, financeiro e elétrica) | `src/guardrails/` |
| Casos de teste e comparação antes e depois | `evals/` |
| Comparação de modelos (gpt-oss:120b e qwen3:8b) | `docs/relatorio_modelos.md` |
| Bônus: vários modelos e prompts ao mesmo tempo | `src/chain/multi_provider.py` |
| Relatório de evolução | `docs/relatorio_evolucao.pdf` |

### Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # no Windows: copy .env.example .env

ollama pull gpt-oss:120b
ollama pull qwen3:8b

python -m src.cli                        # conversa no terminal
python -m evals.demo_memoria             # memória em vários turnos
python -m evals.executar_tudo            # roda todos os casos e gera os resultados
python docs/gerar_relatorio.py           # gera o PDF do relatório
python -m evals.multi_provider_demo      # bônus
```

Se estiver usando o Ollama Cloud, coloque `OLLAMA_BASE_URL` e `OLLAMA_API_KEY` no `.env`. Com uma `GROQ_API_KEY` o eval também roda o código antigo no Groq (Llama 3.3 70B). O `.env` está no `.gitignore`, então as chaves não vão para lugar nenhum.

## Sprint 04: RAG com ChromaDB e interface web

Na Sprint 04 o chatbot ganhou uma base de conhecimento de verdade. Em vez de responder só com os dados fixos no código, agora ele busca em quatro documentos do condomínio (manual do carregador, regimento de recarga compartilhada, tabela de tarifas e perguntas frequentes) antes de responder, e sempre cita de onde tirou a informação.

| O que o enunciado pede | Onde está |
|---|---|
| Base de conhecimento em PDF | `data/knowledge_base/` |
| Vetorização com ChromaDB persistente e nomic-embed-text | `src/rag/embeddings.py` e `src/rag/vector_store.py` |
| Pipeline RAG completo (loader, chunking, retriever, prompt) | `src/rag/` |
| Grounding e citação de fonte | `src/rag/prompt_rag.py` e `src/rag/chain.py` |
| Avaliação (RAGAS ou fallback manual) | `evals/rag_eval_set.py`, `evals/avaliador_rag.py` e `src/rag/metricas.py` |
| Interface web | `app/app.py` |
| Segurança (fora de contexto e instrução escondida em documento) | `src/guardrails/rag_injection.py` e `src/rag/chain.py` |
| Prompt RAG versionado | `prompts/rag_prompt_v1.md`, `prompts/rag_prompt_v2.md` e a seção RAG de `prompts/VERSOES.md` |
| Comparação de modelos para o RAG | `docs/relatorio_modelos.md` |
| Bônus: vários modelos e prompts ao mesmo tempo | `src/rag/multi_provider.py` |
| Relatório de evolução | `docs/relatorio_evolucao.pdf` |

### Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # no Windows: copy .env.example .env

ollama pull gpt-oss:120b
ollama pull qwen3:8b
ollama pull nomic-embed-text

python data/knowledge_base/gerar_pdfs.py   # só precisa rodar uma vez, gera os PDFs da base
python -m src.rag.indexar --versao v2      # vetoriza e guarda no ChromaDB (data/chroma_db/)
python -m src.rag_cli                      # conversa no terminal
python app/app.py                          # interface web (abre em localhost)
python -m evals.executar_rag               # roda as duas iterações e os dois modelos
python docs/gerar_relatorio.py             # gera o PDF do relatório
python -m evals.multi_provider_rag_demo    # bônus
```

A pasta `data/chroma_db/` é gerada localmente (está no `.gitignore`), então rode o `indexar` antes de usar o CLI ou a interface. Se estiver usando o Ollama Cloud, o `nomic-embed-text` também roda por lá, não precisa de nada a mais além do `OLLAMA_BASE_URL` e da `OLLAMA_API_KEY` já configurados.

O RAGAS não funcionou neste projeto (dá erro de import numa dependência que a versão atual do langchain-community não tem mais), então a avaliação usa o fallback manual que o próprio enunciado permite: faithfulness conferindo se os números da resposta aparecem no contexto recuperado, e answer relevancy por similaridade de embeddings entre a pergunta e a resposta. Os detalhes estão em `docs/relatorio_rag.md`.

## Problema

Condomínios que instalam eletropostos GoodWe acabam enfrentando vários problemas no dia a dia. Quando muitos moradores tentam carregar o carro ao mesmo tempo, a rede elétrica do prédio pode sobrecarregar. Além disso, não existe um jeito simples de saber quem usou qual estação e quanto cada um gastou, então o síndico precisa fazer tudo no manual, o que gera confusão na hora de dividir a conta de luz.

Fora isso, quando algo dá errado com uma estação, o morador não tem nenhum canal rápido para tirar dúvida ou reportar o problema.

## O que o chatbot faz?

O ChargeOps Assistant é um chatbot com inteligência artificial feito para ajudar as pessoas que vivem ou trabalham em condomínios com eletropostos GoodWe. A ideia é ter um assistente que responde perguntas, ajuda a agendar recargas, mostra o consumo de cada morador e orienta em caso de falha no equipamento.

O chatbot atende três tipos de usuário. O morador que quer saber se tem estação livre, agendar um horário ou ver quanto gastou no mês. O síndico que precisa de relatórios de consumo, quer configurar limites de potência ou entender como funciona o faturamento. E o técnico de manutenção que precisa de informações sobre falhas e procedimentos para resolver problemas nos equipamentos.

## Tecnologias

Na Sprint 1 a ideia era usar o GPT-4o da OpenAI. Na Sprint 2, como não tínhamos créditos na OpenAI, trocamos para o Llama 3.3 70B rodando no Groq, que tem um tier gratuito e era uma das opções permitidas pela tarefa ("Llama, OpenAI, Gemini ou outra"). O Llama responde muito bem em português, mantém o contexto da conversa e a qualidade é comparável à do GPT-4o para o nosso caso.

A API do Groq é compatível com o SDK da OpenAI, então usamos a mesma biblioteca `openai`, só mudando a base_url e a chave. Isso facilita trocar de modelo no futuro sem reescrever o código.

Na Sprint 2 implementamos um protótipo funcional em Python que já roda no Google Colab. Ele injeta o system prompt com o contexto da GoodWe, guarda o histórico da conversa (numa lista de mensagens que é enviada ao modelo a cada pergunta) e responde com base nos dados de recarga. Os dados da GoodWe estão simulados no código, já que ainda não temos acesso à API real.

A arquitetura completa para a versão de produção (backend em FastAPI, histórico no PostgreSQL, cache de sessão no Redis, orquestração com LangChain e interface em React embutida no portal do condomínio) é o plano futuro do projeto. Para o protótipo desta sprint usamos só o necessário para o chatbot conversar de forma coerente.

## Como executar

### No Google Colab (recomendado)

1. Abra um novo notebook no Google Colab.
2. Instale a biblioteca da OpenAI numa célula:
   ```
   !pip install openai
   ```
3. Adicione sua chave do Groq nos **Secrets** do Colab (ícone de chave na barra lateral), com o nome `GROQ_API_KEY`. Não escreva a chave direto no código.
4. Cole o conteúdo do `chatbot.py` numa célula e rode.
5. Chame `conversar()` para iniciar o chat, ou `rodar_testes()` para rodar os casos de teste de uma vez.

### Em uma IDE (VS Code, PyCharm, etc.)

1. Instale a dependência:
   ```
   pip install openai
   ```
2. Defina a variável de ambiente com sua chave:
   ```
   export GROQ_API_KEY="sua-chave-aqui"      # Linux/Mac
   set GROQ_API_KEY=sua-chave-aqui           # Windows
   ```
3. Rode o arquivo:
   ```
   python chatbot.py
   ```

## Dependências

- Python 3.10 ou superior
- biblioteca `openai`

## Variáveis de ambiente

- `GROQ_API_KEY` - chave de acesso à API do Groq. No Colab, vai nos Secrets; fora do Colab, na variável de ambiente. A chave nunca aparece no código nem no repositório.

## Exemplo de uso

```
Você: oi, tem alguma estação livre agora?
Assistente: No momento temos duas estações disponíveis: a CHR-001 e a CHR-004.
A CHR-002 está em uso (deve liberar por volta das 19:45) e a CHR-003 está fora
do ar por uma falha. Quer iniciar uma recarga agora ou prefere agendar um horário?

Você: quanto vou pagar esse mês? sou do apto 202
Assistente: Em maio o apto 202 consumiu 31,1 kWh no total...
(o chatbot mostra a conta separando pico e fora de pico e dá uma dica de economia)
```

## Estrutura do repositório

```
projeto/
    chatbot.py                 # versão das Sprints 1 e 2
    prompts/                   # system_prompt_v1/v2/v3, rag_prompt_v1/v2 e VERSOES.md
    data/
        knowledge_base/        # os 4 PDFs da base de conhecimento e o script que gera eles
        chroma_db/              # banco vetorial, gerado localmente, não vai pro repositório
    src/
        chain/                  # builder.py, memoria.py, tokens.py, multi_provider.py (Sprint 03)
        schemas/                # consulta_recarga.py
        guardrails/             # scope_validator.py, moderation.py e rag_injection.py
        dados/                  # dados simulados da GoodWe
        rag/                    # loader, chunking, embeddings, vector_store, retriever, prompt_rag, chain
        cli.py, rag_cli.py
        config.py
    app/                        # interface web em Gradio
    evals/                      # casos de teste, execução e comparação, do jeito conversacional e do RAG
    docs/                       # relatório de evolução, relatório do RAG e relatório de modelos
    modelo_de_teste.md, resultados_testes.md, system_prompt.md, fluxograma_chargebot.png
    requirements.txt, .env.example, integrantes.txt
```
