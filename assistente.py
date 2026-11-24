import json
import ollama
from dados import listar_gpus, buscar_gpu
from ferramentas import ferramenta_listar, ferramenta_buscar

instrucao = """Voce e o assistente de um time que compartilha GPUs.
Para perguntas sobre GPUs, consulte a ferramenta uma vez. Depois que receber o resultado, escreva a resposta final em português, sem chamar a ferramenta de novo.

Quando usar listar_gpus: mostre TODAS as GPUs da lista, uma por linha, com total, quantas estao livres agora e a memoria. Nao escolha apenas uma.

Quando usar buscar_gpu:
- se 'disponíveis' for 0, diga que existem GPUs desse modelo, mas nenhuma esta livre agora;
- se 'disponíveis' for maior que 0, diga quantas estao livres;
- se o resultado for null, diga que esse modelo nao existe na infraestrutura e nao fale de disponibilidade.
Se a pergunta nao for sobre GPUs (por exemplo um cumprimento), responda normalmente com um cumprimento e pergunte como você pode ajudar, sem usar ferramentas.

"""

# o historico comeca so com a instrucao e vai crescendo com a conversa
mensagens = [{"role": "system", "content": instrucao}]

funcoes = {
    "buscar_gpu": buscar_gpu,
    "listar_gpus": listar_gpus,
}
if __name__ == "__main__":
    while True:
        pergunta = input("Você: ")

        if pergunta.strip().lower() == "sair":
            break

        if pergunta.strip() == "":
            continue

        mensagens.append({"role": "user", "content": pergunta})

        # primeira chamada: o modelo decide se precisa de ferramenta
        resposta = ollama.chat(
            model="llama3.2",
            messages=mensagens,
            tools=[ferramenta_listar, ferramenta_buscar],
            options={"temperature": 0},
        )

        pedidos = resposta.message.tool_calls
        print(">>> pedidos:", pedidos)

        if pedidos:
            primeiro = pedidos[0]
            funcao_pedida = primeiro.function.name
            argumentos = primeiro.function.arguments

            # executa a funcao q o modelo pediu
            resultado = funcoes[funcao_pedida](**argumentos)

            # o pedido do modelo entra no historico
            mensagens.append(resposta.message)

            mensagens.append({
                "role": "tool",
                "tool_name": funcao_pedida,
                "content": json.dumps(resultado, ensure_ascii=False),
            })

            # segunda chamada: sem tools, ele so escreve a resposta final
            final = ollama.chat(
                model="llama3.2",
                messages=mensagens,
                options={"temperature": 0},
            )
            print(final.message.content)

            # guarda a resposta final no historico
            mensagens.append(final.message)
        else:
            print(resposta.message.content)
