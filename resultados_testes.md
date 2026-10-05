# Resultados dos Testes - ChargeOps Assistant (Sprint 2)

Aqui registramos a execução dos casos de teste definidos na Sprint 1
(arquivo `modelo_de_teste.md`). Para cada caso anotamos a pergunta enviada,
a resposta que o chatbot deu e uma avaliação qualitativa.

Os testes foram executados com o modelo **Llama 3.3 70B** rodando no Groq,
com `temperature 0.3`. As respostas abaixo são as que o chatbot gerou de fato.

A avaliação usa três níveis:
- **adequada**: respondeu certo, no formato certo pra persona e sem inventar nada.
- **parcialmente adequada**: acertou o principal mas errou algum detalhe.
- **inadequada**: errou os números, a persona ou inventou informação.

---

## Caso 1 - Morador quer saber se tem estação disponível

**Pergunta:** Oi, tem alguma estação de recarga livre agora?

**Resposta obtida:** Informou que as estações CHR-001 e CHR-004 estão disponíveis,
que a CHR-002 está em uso com previsão de liberação às 19h45, e que a CHR-003 está
com erro. Encerrou com uma dica de carregar fora do horário de pico para pagar
tarifa mais baixa.

**Avaliação:** adequada

**Comentário:** Identificou a intenção, apresentou o status de forma clara e deu
um próximo passo. Único ponto a melhorar: mencionou o código "E05 / falha no
aterramento" para um morador, o que é um pouco técnico demais para essa persona.

---

## Caso 2 - Morador perguntando quanto vai pagar

**Pergunta:** quanto vou pagar de recarga esse mês? eu sou do apto 202

**Resposta obtida:** Calculou 22,9 kWh x R$ 0,75 = R$ 17,18 (fora de pico) e
8,2 kWh x R$ 1,30 = R$ 10,66 (pico), totalizando R$ 27,84. Explicou que a taxa de
infraestrutura é dividida entre todos e não entra direto nesse valor, e fechou
com uma dica de economia.

**Avaliação:** adequada

**Comentário:** Diferenciou pico e fora de pico, mostrou toda a conta, usou
linguagem simples e deu dica de economia. Os números bateram exatamente com o
esperado no modelo de teste.

---

## Caso 3 - Morador quer saber o melhor horário para carregar

**Pergunta:** qual o melhor horário para eu recarregar hoje à noite?

**Resposta obtida:** Recomendou recarregar após as 21h, quando a tarifa cai para
R$ 0,75, e explicou que a ocupação é menor (20% às 22h e 10% às 23h).

**Avaliação:** parcialmente adequada

**Comentário:** Combinou os dois fatores (tarifa e ocupação) e usou linguagem
simples, mas faltou quantificar a economia em reais e oferecer agendar a recarga,
que o modelo de teste pedia.

---

## Caso 4 - Síndico pedindo resumo do mês

**Pergunta:** me dá um resumo do consumo de todos os apartamentos em maio

**Resposta obtida (após iteração):** Listou o consumo dos quatro apartamentos,
calculou a média (40,8 kWh) e apontou sozinho que o Apto 303 está cerca de 66%
acima da média, tratando como possível anomalia. Calculou os custos corretos
(R$ 49,78 / R$ 27,84 / R$ 64,41 / R$ 11,40) e ofereceu gerar o relatório para a
administradora.

**Avaliação:** adequada

**Comentário:** Números corretos, identificou a anomalia do 303 automaticamente e
ofereceu o próximo passo. Esse caso só ficou adequado depois de ajustarmos o
system prompt (ver seção "Iterações realizadas").

---

## Caso 5 - Síndico pedindo o rateio do mês

**Pergunta:** como fica o rateio desse mês? quero colocar na taxa condominial de cada apartamento

**Resposta obtida:** Separou o custo de energia do custo de infraestrutura,
calculou o consumo por unidade e rateou os R$ 80,00 de infraestrutura
proporcionalmente ao consumo de cada apartamento, mostrando o total por unidade.

**Avaliação:** parcialmente adequada

**Comentário:** Separou energia de infraestrutura e explicou a metodologia, mas
dividiu a taxa de infraestrutura de forma proporcional ao consumo, enquanto o
modelo de teste esperava a divisão igual entre as quatro unidades. Também não
sinalizou diferença em relação à fatura da concessionária. A divisão por consumo
é defensável, mas diverge do esperado.

---

## Caso 6 - Técnico com carregador com falha

**Pergunta:** o carregador CHR-003 está com problema, o que está acontecendo?

**Resposta obtida:** Informou o status de erro com código E05 (GroundFailure),
o histórico (última falha em 18/05 às 14:32, última sessão ok em 17/05 às 09:15,
4 ocorrências nos últimos 7 dias) e recomendou contato com o suporte técnico da
GoodWe.

**Avaliação:** parcialmente adequada

**Comentário:** Apresentou os dados de erro e o histórico corretamente e seguiu a
regra de recomendar o suporte para problemas graves. Faltou o passo a passo de
diagnóstico (isolar circuito, medir continuidade do PE, verificar o DR), mas isso
acontece porque esse procedimento não está nos dados simulados que injetamos.
O chatbot agiu certo ao não inventar esses passos.

---

## Caso 7 - Pergunta fora do escopo

**Pergunta:** qual o melhor carro elétrico para comprar em 2025?

**Resposta obtida (após iteração):** "Essa pergunta foge um pouco do que eu faço
por aqui, que é cuidar das recargas e estações do seu condomínio. Posso te ajudar
a ver seu consumo do mês, conferir se tem estação livre ou agendar uma recarga.
Quer alguma dessas?"

**Avaliação:** adequada

**Comentário:** Reconheceu que a pergunta está fora do escopo, não tentou
responder nem listou modelos de carro, e redirecionou para o que sabe fazer.
Esse caso também só ficou adequado depois do ajuste no system prompt.

---

## Iterações realizadas

Rodando os testes pela primeira vez, dois casos não saíram como o esperado:

- **Caso 4:** o chatbot dava os números certos, mas não apontava sozinho que o
  Apto 303 estava acima da média e não oferecia gerar o relatório.
- **Caso 7:** em vez de recusar a pergunta fora do escopo, o chatbot respondia e
  até listava modelos de carro.

Com base nisso, ajustamos o system prompt:

1. Tornamos a regra de resumo obrigatória: ao resumir várias unidades, o chatbot
   deve calcular a média, apontar a unidade acima dela e oferecer o relatório.
2. Endurecemos a regra de escopo, proibindo responder a perguntas fora do tema, e
   incluímos um exemplo de recusa correta dentro do prompt (técnica de few-shot
   prompting).

Depois do ajuste, os Casos 4 e 7 passaram a sair adequados, como mostrado acima.

---

## Conclusão dos testes

Dos 7 casos, 4 saíram adequados (1, 2, 4 e 7) e 3 parcialmente adequados (3, 5 e 6).
Em todos os casos os cálculos de consumo e custo bateram com o esperado. Os pontos
parcialmente adequados são principalmente de comportamento (quantificar economia,
método de rateio) ou de dados que não estão no contexto simulado (passo a passo de
diagnóstico). Os dois casos que falharam na primeira rodada foram corrigidos com
ajustes no system prompt, o que mostra o ciclo de teste e iteração.
