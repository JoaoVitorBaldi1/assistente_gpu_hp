import ollama

ferramenta_listar = {
    "type": "function",
    "function": {
        "name": "listar_gpus",
        "description": "Retorna uma lista onde cada elemento da lista é uma gpu, quantas dela temos no total, quanto de momória em GB esse modelo de gpu tem e quantas temos dsponíveis no momento, Use somente quando o cliente perguntar quais livros existem. Não use para cumprimentos ou assuntos que não sejam sobre livros.",
        "parameters": {"type": "object", "properties": {}},
    },
}

ferramenta_buscar = {
    "type": "function",
    "function": {
        "name": "buscar_gpu",
        "description": "Busca as informações de uma GPU da infraestrutura. Aceita o nome com ou sem 'NVIDIA'. Retorna quantidade total na infraestrutura, a quantidade disponível e quanto de memória o moedelo tem em GB, ou nulo se não existir.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome_gpu": {
                    "type": "string",
                    "description": "Nome da GPU que o usuário quer consultar, por exemplo A100 ou NVIDIA H100",
                }
            },
            "required": ["nome_gpu"],
        },
    },
}