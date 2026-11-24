import json

import ollama
import pandas as pd
import streamlit as st

from assistente import instrucao
from dados import dados, listar_gpus, buscar_gpu
from ferramentas import ferramenta_listar, ferramenta_buscar

MODELO = "llama3.2"

# nome (texto) -> funcao de verdade
funcoes = {
    "buscar_gpu": buscar_gpu,
    "listar_gpus": listar_gpus,
}


def responder(mensagens):
    """Mesma logica do assistente.py: o modelo pede a ferramenta, o codigo executa
    e o resultado volta pro modelo escrever a resposta final.
    Devolve o texto final e um resumo da consulta feita (ou None)."""
    resposta = ollama.chat(
        model=MODELO,
        messages=mensagens,
        tools=[ferramenta_listar, ferramenta_buscar],
        options={"temperature": 0},
    )

    pedidos = resposta.message.tool_calls

    # nao pediu ferramenta: ja respondeu em texto
    if not pedidos:
        mensagens.append(resposta.message)
        return resposta.message.content, None

    primeiro = pedidos[0]
    nome_funcao = primeiro.function.name
    argumentos = primeiro.function.arguments

    resultado = funcoes[nome_funcao](**argumentos)

    mensagens.append(resposta.message)
    mensagens.append({
        "role": "tool",
        "tool_name": nome_funcao,
        "content": json.dumps(resultado, ensure_ascii=False),
    })

    # segunda chamada: sem tools, so escreve a resposta final
    final = ollama.chat(
        model=MODELO,
        messages=mensagens,
        options={"temperature": 0},
    )
    mensagens.append(final.message)

    consulta = (
        f"Funcao: {nome_funcao}\n"
        f"Argumentos: {argumentos}\n"
        f"Resultado: {json.dumps(resultado, ensure_ascii=False, indent=2)}"
    )
    return final.message.content, consulta


# ---------- interface ----------

st.set_page_config(page_title="Assistente de GPUs", page_icon="🖥️")
st.title("🖥️ Assistente de GPUs")
st.caption("Pergunte sobre as GPUs do time. As respostas vêm dos dados do sistema.")

# o streamlit roda o arquivo inteiro a cada interacao, entao o historico fica no session_state
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [{"role": "system", "content": instrucao}]  # historico do modelo
if "chat" not in st.session_state:
    st.session_state.chat = []  # o que aparece na tela

with st.sidebar:
    st.subheader("Dados do sistema")
    st.caption("Para conferir as respostas do assistente.")
    st.dataframe(pd.DataFrame(dados).T)

    if st.button("Limpar conversa"):
        st.session_state.mensagens = [{"role": "system", "content": instrucao}]
        st.session_state.chat = []
        st.rerun()

# mostra a conversa ate agora
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("consulta"):
            with st.expander("Consulta feita ao sistema"):
                st.code(msg["consulta"])

pergunta = st.chat_input("Ex.: Quais GPUs estão livres?")

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    st.session_state.chat.append({"role": "user", "content": pergunta})

    tamanho_antes = len(st.session_state.mensagens)
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            try:
                texto, consulta = responder(st.session_state.mensagens)
            except Exception as erro:
                # volta o historico do modelo pro estado de antes da pergunta
                del st.session_state.mensagens[tamanho_antes:]
                texto = "Não consegui responder agora. Confere se o Ollama está aberto e tenta de novo."
                consulta = None
                st.error(f"Erro: {erro}")

        st.markdown(texto)
        if consulta:
            with st.expander("Consulta feita ao sistema"):
                st.code(consulta)

    st.session_state.chat.append({"role": "assistant", "content": texto, "consulta": consulta})
