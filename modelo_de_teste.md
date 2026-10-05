# Modelo de Teste - ChargeOps Assistant

Esse arquivo contém as perguntas que esperamos que os usuários façam e como o chatbot deveria responder em cada caso. Vai ser usado na Sprint 2 para avaliar se o chatbot está se comportando do jeito certo.

Cada caso vai receber nota de 0 a 10 considerando: os números estão certos, identificou a persona corretamente, usou o formato de resposta adequado para a persona, deu alguma sugestão de continuidade, e não inventou nenhuma informação que não estava no contexto.

## Caso 1 - Morador quer saber se tem estação disponível

Pergunta: Oi, tem alguma estação de recarga livre agora?

Resposta esperada: O chatbot deve verificar o status atual das estações e informar quais estão livres e quais estão em uso. Se alguma estiver em uso, o ideal é informar uma previsão de quando vai liberar. No final, deve perguntar se o usuário quer iniciar uma recarga agora ou prefere agendar um horário.

O que avaliar: identificou a intenção corretamente, apresentou o status das estações de forma clara e ofereceu um próximo passo para o usuário.

## Caso 2 - Morador perguntando quanto vai pagar

Pergunta: quanto vou pagar de recarga esse mês?

Contexto simulado: Apto 202, total de 31,1 kWh. Recargas fora do pico: 22,9 kWh. Recargas no horário de pico (18h-21h): 8,2 kWh.

Resposta esperada: Até agora em maio o seu apartamento consumiu 31,1 kWh no total. As recargas fora do horário de pico foram 22,9 kWh. A tarifa nesses horários é R$ 0,75, então ficou R$ 17,18. As recargas no horário de pico foram 8,2 kWh. Nesse horário a tarifa é R$ 1,30, então ficou R$ 10,66. Total estimado até agora: R$ 27,84. Se você conseguir carregar depois das 21h ou antes das 18h vai economizar bastante.

O que avaliar: diferenciou tarifa de pico e fora de pico corretamente, mostrou a conta, usou linguagem simples sem termos técnicos e deu dica de economia.

## Caso 3 - Morador quer saber o melhor horário para carregar

Pergunta: qual o melhor horário para eu recarregar hoje à noite?

Contexto simulado: das 18h às 20h a ocupação está entre 78% e 90% com tarifa de R$ 1,30. Às 21h a ocupação cai para 45% e a tarifa vai para R$ 0,75. Às 22h ocupação de 20% e às 23h de 10%, ambas com tarifa R$ 0,75.

Resposta esperada: O chatbot deve recomendar a partir das 22h ou 23h, explicar que das 18h às 21h a tarifa é mais cara e os carregadores ficam mais ocupados, quantificar a economia em reais com base no padrão de uso do morador e oferecer agendamento automático.

O que avaliar: combinou os dois fatores de tarifa e disponibilidade, quantificou a economia, usou linguagem simples e ofereceu uma próxima ação.

## Caso 4 - Síndico pedindo resumo do mês

Pergunta: me dá um resumo do consumo de todos os apartamentos em maio

Contexto simulado: Apto 101 com 52,4 kWh em 18 sessões, Apto 202 com 31,1 kWh em 9 sessões, Apto 303 com 67,8 kWh em 24 sessões, Apto 404 com 12,0 kWh em 4 sessões. Tarifa base R$ 0,95.

Resposta esperada: O chatbot deve listar o consumo e o custo de cada apartamento com os cálculos corretos, identificar que o Apto 303 consumiu bem acima da média sem precisar ser perguntado e oferecer gerar o relatório para a administradora.

O que avaliar: números corretos, identificou a anomalia do 303 automaticamente, usou linguagem gerencial e ofereceu uma próxima ação.

## Caso 5 - Síndico pedindo o rateio do mês

Pergunta: como fica o rateio desse mês? quero colocar na taxa condominial de cada apartamento

Contexto simulado: Apto 101 R$ 49,78, Apto 202 R$ 27,84, Apto 303 R$ 64,41, Apto 404 R$ 11,40 de energia. Taxa mensal de infraestrutura dos carregadores de R$ 80,00 dividida entre as quatro unidades.

Resposta esperada: O chatbot deve separar o custo de energia do custo de infraestrutura, mostrar o total por apartamento, identificar e sinalizar qualquer diferença entre os valores calculados e a fatura da concessionária e recomendar como ajustar antes de lançar na taxa.

O que avaliar: explicou a metodologia, separou energia de infraestrutura, identificou diferença nos valores e sugeriu como resolver.

## Caso 6 - Técnico com carregador com falha

Pergunta: o carregador CHR-003 está com problema, o que está acontecendo?

Contexto simulado: Status erro, código E05, descrição GroundFailure, última sessão com erro em 18/05/2026 às 14:32, última sessão bem-sucedida em 17/05/2026 às 09:15, quatro ocorrências do erro nos últimos 7 dias.

Resposta esperada: O chatbot deve informar o código de erro e o que ele significa, apresentar o histórico de ocorrências, dar o procedimento de diagnóstico em ordem de prioridade (isolar o circuito, medir continuidade do condutor PE, verificar o DR do CHR-003) e oferecer gerar um relatório de incidente para protocolar com o fabricante.

O que avaliar: usou terminologia técnica corretamente, apresentou os dados brutos do contexto, deu orientação de diagnóstico em ordem de prioridade e sinalizou o risco de segurança.

## Caso 7 - Pergunta fora do escopo

Pergunta: qual o melhor carro elétrico para comprar em 2025?

Resposta esperada: O chatbot deve reconhecer que a pergunta está fora do escopo de forma educada, sem tentar responder. Deve redirecionar para o que sabe fazer, como verificar disponibilidade de estações, consultar consumo ou agendar uma recarga.

O que avaliar: não inventou uma resposta fora do contexto, foi educado ao recusar e redirecionou para o escopo correto.
