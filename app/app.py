import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr

from src import config
from src.chain.builder import criar_llm
from src.rag.chain import RagAssistant
from src.rag.embeddings import criar_embeddings

_assistente = None


def obter_assistente():
    global _assistente
    if _assistente is None:
        llm = criar_llm(config.MODELO_PRINCIPAL, temperature=0.0)
        embeddings = criar_embeddings()
        _assistente = RagAssistant(llm, embeddings=embeddings, versao=config.VERSAO_RAG_PADRAO)
    return _assistente


def formatar_fontes(resultado):
    if resultado.fora_do_contexto or not resultado.fontes:
        return "_nenhuma fonte usada nesta resposta_"
    linhas = ["**Fontes usadas:**", ""]
    for f in resultado.fontes:
        linhas.append(f"- {f['documento']} - {f['secao']} (relevância {f['relevancia']:.2f})")
    linhas.append("")
    linhas.append(
        f"faithfulness: {resultado.faithfulness:.2f}, answer relevancy: {resultado.answer_relevancy:.2f}, "
        f"citação no texto: {'sim' if resultado.citacao_presente else 'não'}"
    )
    if resultado.linhas_neutralizadas:
        linhas.append(
            f"⚠️ {resultado.linhas_neutralizadas} trecho(s) neutralizado(s) por conter possível instrução escondida"
        )
    return "\n".join(linhas)


def responder(pergunta, historico):
    historico = historico or []
    if not pergunta or not pergunta.strip():
        return historico, "", gr.update()
    assistente = obter_assistente()
    resultado = assistente.perguntar(pergunta)
    historico = historico + [
        {"role": "user", "content": pergunta},
        {"role": "assistant", "content": resultado.texto},
    ]
    return historico, "", formatar_fontes(resultado)


with gr.Blocks(title="ChargeOps RAG") as demo:
    gr.Markdown(
        "# ChargeOps Assistant - base de conhecimento\n"
        "Pergunte sobre o manual do carregador, o regimento de recarga compartilhada, "
        "a tabela de tarifas ou as perguntas frequentes. As respostas vêm só da base de "
        "conhecimento e sempre citam a fonte."
    )
    with gr.Row():
        with gr.Column(scale=2):
            chat = gr.Chatbot(height=480, label="Conversa")
            entrada = gr.Textbox(placeholder="Digite sua pergunta e aperte Enter", label="Pergunta")
        with gr.Column(scale=1):
            fontes = gr.Markdown("_as fontes da resposta aparecem aqui_", label="Fontes")

    entrada.submit(responder, [entrada, chat], [chat, entrada, fontes])


if __name__ == "__main__":
    demo.launch()
