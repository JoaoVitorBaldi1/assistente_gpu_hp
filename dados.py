dados = {
    "NVIDIA A100" : {"total":4,"memoria_gb":80, "disponíveis":4},
    "NVIDIA L40S" : {"total":6, "memoria_gb": 48,"disponíveis":4},
    "NVIDIA RTX 4090" : {"total":3, "memoria_gb":24,"disponíveis":1},
    "NVIDIA H100" : {"total":2, "memoria_gb":80, "disponíveis":0},
    "NVIDIA A40" : {"total":4, "memoria_gb":48, "disponíveis":3}
}

def listar_gpus():
    linhas = []

    for nome, info in dados.items():
        linha = f"{nome}: {info['total']} no total, {info['disponíveis']} livres agora, {info['memoria_gb']} GB de memoria cada"
        linhas.append(linha)

    return linhas

def buscar_gpu(nome_gpu):
    nome_gpu = nome_gpu.strip().upper()

    nomes = list(dados.keys())

    for gpu in nomes:
        nome_completo = gpu.upper()
        nome_curto = nome_completo.replace("NVIDIA ","")

        if nome_gpu == nome_completo or nome_gpu == nome_curto:
            return dados[gpu]
    return None
