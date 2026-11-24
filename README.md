# Assistente de IA para consulta de GPUs

Assistente conversacional (no terminal e em uma interface web) que responde perguntas sobre as GPUs compartilhadas por um time: quais existem, quantas há no total, quantas estão livres agora e quanta memória cada modelo tem.

Feito para o desafio de estágio em Machine Learning / AI. O modelo de linguagem roda **localmente** (Ollama + llama3.2), sem APIs pagas.

## A ideia principal

O modelo de linguagem **não sabe nada sobre a infraestrutura**. Se ele respondesse de cabeça, iria inventar. Por isso ele nunca responde direto: quando a pergunta é sobre GPUs, ele *pede* uma consulta ao sistema (técnica chamada *tool calling*), o meu código executa a consulta nos dados reais e devolve o resultado, e só então o modelo escreve a resposta final.

```
Usuário: "Tem RTX 4090 livre?"
   │
   ▼
Modelo decide: preciso consultar -> pede buscar_gpu(nome_gpu="RTX 4090")
   │
   ▼
Meu código executa buscar_gpu e acha os dados no dicionário
   │
   ▼
O resultado volta ao modelo como mensagem de ferramenta
   │
   ▼
Modelo escreve a resposta final em português
```

Dessa forma, números como quantidade e disponibilidade vêm sempre dos dados do sistema, não do modelo.

## Estrutura do projeto

| Arquivo | O que faz |
|---|---|
| `dados.py` | Guarda as GPUs (dicionário) e as funções de consulta `listar_gpus()` e `buscar_gpu(nome_gpu)` |
| `ferramentas.py` | Descrição das duas ferramentas no formato que o modelo entende (nome, para que servem, argumentos) |
| `assistente.py` | Chat no terminal: manda a conversa ao modelo, executa a ferramenta que ele pedir e imprime a resposta. Também guarda a instrução de sistema, que a interface web reaproveita |
| `app.py` | Interface web (Streamlit): mesma lógica do chat do terminal, com balões de conversa, tabela dos dados e a consulta feita ao sistema em cada resposta |
| `requirements.txt` | Dependências Python (`ollama` e `streamlit`) |

## Como executar

Testado no Windows com Python 3.14.

1. **Instalar o Ollama**: baixe em <https://ollama.com/download> e instale.
2. **Baixar o modelo** (cerca de 2 GB):
   ```
   ollama pull llama3.2
   ```
3. **Instalar as dependências Python**:
   ```
   pip install -r requirements.txt
   ```
4. **Rodar** (o Ollama precisa estar aberto em segundo plano). Há duas formas:

   Interface web (abre no navegador):
   ```
   streamlit run app.py
   ```

   Ou chat no terminal (para encerrar, digite `sair`):
   ```
   python assistente.py
   ```

No terminal aparecem linhas começando com `>>> pedidos:`. Elas mostram qual ferramenta o modelo pediu e foram deixadas de propósito como modo de depuração. Na interface web, o mesmo aparece dentro de cada resposta, no item "Consulta feita ao sistema".

## Dados simulados

Os recursos do enunciado foram simulados em `dados.py`. O enunciado só traz quantidade e memória, então **criei o campo `disponíveis`** com valores inventados, para o assistente conseguir responder se algo está livre ou não.

| GPU | Total | Memória (GB) | Livres (simulado) |
|---|---|---|---|
| NVIDIA A100 | 4 | 80 | 4 |
| NVIDIA L40S | 6 | 48 | 4 |
| NVIDIA RTX 4090 | 3 | 24 | 1 |
| NVIDIA H100 | 2 | 80 | 0 |
| NVIDIA A40 | 4 | 48 | 3 |

A H100 ficou com 0 livres de propósito, para testar o caso "existe, mas está tudo ocupado".

## Decisões de projeto

- **Tool calling em vez de colocar os dados no prompt.** O modelo só vê o resultado das consultas, então não tem como "lembrar" um número errado. Também facilita trocar os dados por um banco real no futuro.
- **Duas ferramentas simples**: `listar_gpus` (visão geral) e `buscar_gpu` (uma GPU específica). A busca aceita o nome com ou sem "NVIDIA" e ignora maiúsculas e espaços (`"a100"`, `"NVIDIA A100"`).
- **Resultado "não encontrado" explícito.** Quando a GPU não existe, a função devolve `None` (vira `null` para o modelo) e a instrução de sistema diz que isso significa "esse modelo não existe na infraestrutura". Sem essa regra o modelo confundia "não existe" com "está tudo em uso".
- **`listar_gpus` devolve uma frase por GPU**, por exemplo `NVIDIA H100: 2 no total, 0 livres agora, 80 GB de memoria cada`. Quando devolvia um dicionário dentro de outro, o modelo pequeno pegava só uma GPU e respondia sobre ela. As frases resolveram. Quem escolhe quais dados mostrar continua sendo o meu código, o modelo só reescreve.
- **Palavra "livres" em vez de "disponíveis" no resultado da lista.** Em um teste o modelo respondeu "não há informações disponíveis" ao ler `disponíveis: 0`, misturando os dois sentidos.
- **Instrução de sistema com uma seção por ferramenta**, dizendo o que fazer em cada caso (0 livres, mais de 0 livres, não encontrada) e que cumprimentos não precisam de ferramenta.
- **`temperature = 0`** nas duas chamadas ao modelo, para reduzir a variação entre execuções e deixar os testes comparáveis.
- **Duas chamadas ao modelo por pergunta**: a primeira com as ferramentas disponíveis (ele decide se precisa delas), a segunda sem ferramentas, só para escrever a resposta final.
- **Histórico completo mantido durante a conversa**, incluindo as respostas do assistente, para perguntas como "e a A100?" fazerem sentido.

## Como testei

Usei uma tabela de perguntas com o comportamento esperado e a rodei de novo **a cada mudança na instrução de sistema**, porque ajustar o prompt chegou a quebrar casos que já funcionavam.

| Pergunta | Comportamento esperado | Resultado |
|---|---|---|
| Temos NVIDIA H100 disponível? | Existe, mas nenhuma livre agora | ✅ |
| Existem duas A100 disponíveis? | Sim, 4 livres | ✅ |
| Tem RTX 4090 livre? | Sim, 1 livre (de 3) | ✅ |
| Vocês têm RTX 5090? | Não existe na infraestrutura | ✅ |
| Quais GPUs temos? | Lista as 5, com total, livres e memória | ✅ |
| Quais GPUs estão livres? | Só as que têm livres (a H100 não entra) | ✅ |
| Oi, tudo bem? | Cumprimenta e pergunta como ajudar | ✅ |
| Sequência: "Quais GPUs estão livres?", "E a A100?", "E a H100?" | Entende que as perguntas seguintes continuam a conversa | ✅ |

## Problemas encontrados no caminho

Registro do que deu errado e como entendi cada causa:

- **Chamada de ferramenta escrita como texto.** Às vezes o modelo digitava o pedido (`{"name": "buscar_gpu", ...}`) em vez de usar o canal de ferramenta, e o código não reconhecia. Reduzi com `temperature = 0` e uma instrução clara de que, depois de receber o resultado, ele deve escrever a resposta final e não chamar a ferramenta de novo.
- **Modelo inventando.** Sem a regra para `null`, ele respondia "todas em uso" para uma GPU que não existe. Com resultado vazio ele também completava com conhecimento próprio (chegou a sugerir comandos de nuvem).
- **Regressão ao mexer no prompt.** Mover a regra do cumprimento para o começo da instrução fez o modelo responder "Olá!" a perguntas sobre GPUs.
- **Histórico incompleto.** No começo as respostas do assistente não eram guardadas, o que atrapalhava perguntas de acompanhamento.

## Limitações conhecidas

- O modelo é pequeno (llama3.2, 3B) e, mesmo com `temperature = 0`, não é 100% estável. Pode errar concordância (por exemplo "1 livres") ou, em um cumprimento, chamar a ferramenta sem necessidade (a resposta final ao usuário continua correta).
- Só o **primeiro** pedido de ferramenta de cada vez é executado. Perguntas que exigem várias consultas (por exemplo "qual GPU tem mais memória?") podem não ser respondidas corretamente.
- Se o modelo pedir uma função que não existe ou argumentos errados, o programa para com erro. Ainda não há tratamento de exceções.
- Os dados ficam em memória e a disponibilidade é fixa. Não há reserva de GPU nem controle de **quando** uma GPU será liberada, apenas quantas estão livres agora.
- O histórico cresce durante a conversa, então conversas muito longas podem ficar lentas ou confundir o modelo.
- A interface web guarda a conversa apenas enquanto a página está aberta. Recarregar a página começa uma conversa nova.

## Próximos passos

- Tratar erros (`try/except`) para que uma resposta inesperada do modelo não derrube o chat.
- Ferramenta própria para listar só as GPUs livres.
- Testar um modelo maior (por exemplo `qwen2.5:7b`), se a máquina permitir.
- Trocar o dicionário por um banco de dados e incluir reserva de GPUs.

## Uso de IA

O enunciado permite o uso de assistentes de código. Usei o Claude como apoio de estudo: para entender o conceito de tool calling e revisar o meu código. O código do assistente (dados, ferramentas e chat do terminal) foi escrito e testado por mim. A interface web (`app.py`) foi feita com ajuda de IA, pois frontend não é a minha área, e reaproveita a mesma lógica do chat do terminal.
