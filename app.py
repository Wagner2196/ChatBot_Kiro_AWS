# app.py - Aplicação Flask do KVN, o chatbot educacional de Inteligência Artificial.
# Este arquivo concentra a instância Flask, as rotas e a integração com o Amazon Bedrock.

# Importa o módulo json da biblioteca padrão para serializar o corpo da
# requisição enviada ao Bedrock e desserializar o corpo da resposta recebida.
import json

# Importa o Flask (framework web usado para servir a página e o endpoint de chat)
# e alguns utilitários:
#   - render_template: renderiza a página de chat a partir de templates/index.html
#     (Requisito 1.1);
#   - request: dá acesso ao corpo JSON das requisições recebidas no endpoint de chat;
#   - jsonify: monta respostas JSON (usado nas respostas de erro de validação).
from flask import Flask, render_template, request, jsonify

# Importa o boto3 (SDK da AWS usado para falar com o Amazon Bedrock).
# Se o flask ou o boto3 não estiverem instalados, o próprio Python encerra a execução
# com um ImportError que nomeia qual dependência está ausente (Requisito 7.4).
import boto3

# Importa a classe Config do botocore para ajustar tempos de espera (timeouts)
# e a política de retentativas do cliente Bedrock (Requisito 6.1).
from botocore.config import Config

# Importa as exceções do botocore usadas no tratamento de erros do endpoint de
# chat (Requisitos 5.4, 6.1-6.4):
#   - NoCredentialsError: credenciais da AWS ausentes nas variáveis de ambiente;
#   - ClientError: erro retornado pelo próprio serviço Bedrock;
#   - BotoCoreError: classe base de erros do botocore (abrange, entre outros,
#     ReadTimeoutError de timeout e ConnectTimeoutError de conexão).
# Observação: NoCredentialsError e ReadTimeoutError são subclasses de
# BotoCoreError; capturamos BotoCoreError para cobrir falhas e timeouts, e
# tratamos NoCredentialsError separadamente para exibir a mensagem distinta de
# indisponibilidade do serviço (Requisito 5.4).
from botocore.exceptions import NoCredentialsError, ClientError, BotoCoreError

# Cria a instância da aplicação Flask.
app = Flask(__name__)

# Configura a serialização JSON para NÃO escapar caracteres não-ASCII.
# Assim os acentos (á, ç, ã, ...) aparecem legíveis na resposta JSON,
# em vez de serem convertidos para sequências do tipo \uXXXX (Requisito 2.2).
app.json.ensure_ascii = False

# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------

# Região da AWS onde o Amazon Bedrock será acessado (Requisito 5.1).
REGION = "us-east-1"

# Identificador do modelo de inferência utilizado em todas as chamadas ao
# Bedrock. É o Claude Haiku aprovado para o projeto (Requisito 5.2).
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Número máximo de caracteres aceitos em uma mensagem do usuário.
# Usado tanto na interface quanto na validação do endpoint (Requisitos 1.3 e 3.1).
MAX_CHARS = 2000

# Tempo máximo, em segundos, que aguardamos a resposta do Bedrock antes de
# considerar a chamada como falha por timeout (Requisito 6.1).
TIMEOUT_SEGUNDOS = 30

# ---------------------------------------------------------------------------
# Histórico da conversa (memória)
# ---------------------------------------------------------------------------

# Lista em nível de módulo que guarda, em ordem cronológica, as mensagens do
# usuário e as respostas do KVN trocadas durante a execução do servidor
# (Requisito 8.1). Inicia vazia na partida e é preservada entre requisições
# sucessivas ao /chat na mesma execução (Requisito 8.6). Cada item segue o
# formato da Messages API da Anthropic: {"role": "user"|"assistant",
# "content": [{"type": "text", "text": ...}]}.
conversation_history = []

# ---------------------------------------------------------------------------
# Persona do KVN (SYSTEM_PROMPT)
# ---------------------------------------------------------------------------

# A SYSTEM_PROMPT define a personalidade, o tom e os limites de atuação do KVN.
# Ela é enviada no campo "system" de cada chamada ao Bedrock (Requisito 4.2),
# condicionando todas as respostas ao mesmo comportamento, sem depender de
# histórico de conversa. As instruções abaixo cobrem, de forma explícita:
#   - postura didática de professor para iniciantes, com exemplo quando aplicável
#     (Requisitos 4.1a e 4.3);
#   - humor leve ao responder temas de IA (Requisitos 4.1b e 4.4);
#   - escopo restrito ao estudo de Inteligência Artificial (Requisito 4.1c);
#   - recusa educada e redirecionamento quando o pedido estiver fora de escopo
#     (Requisito 4.5).
SYSTEM_PROMPT = """
Você é o KVN, um professor de Inteligência Artificial. Sua missão é ajudar
quem está estudando IA a aprender de forma clara, acessível e agradável.

Como você deve agir:
- Postura de professor: explique cada conceito de maneira simples, pensando
  em estudantes iniciantes em IA. Use linguagem acessível, evite jargão
  desnecessário e, quando ajudar na compreensão, apresente ao menos um
  exemplo prático do conceito solicitado.
- Humor leve: ao falar sobre temas de IA, inclua um toque de humor leve e
  descontraído, sem nunca comprometer a clareza da explicação.
- Escopo: fale somente sobre estudo de Inteligência Artificial (conceitos,
  técnicas, modelos, aprendizado de máquina, redes neurais, ética em IA,
  ferramentas e temas correlatos de estudo).
- Fora de escopo: se pedirem algo que não seja sobre estudo de Inteligência
  Artificial, recuse com gentileza, NÃO forneça o conteúdo fora de escopo e
  convide a pessoa, de forma simpática, a voltar para assuntos de IA.
""".strip()

# ---------------------------------------------------------------------------
# Cliente do Amazon Bedrock (bedrock-runtime)
# ---------------------------------------------------------------------------

# Configuração de rede do cliente Bedrock.
# Definimos read_timeout e connect_timeout iguais a TIMEOUT_SEGUNDOS (30s) e
# desligamos as retentativas (max_attempts = 0) para que uma chamada que não
# conclua dentro do limite de 30 segundos falhe de imediato, garantindo o
# tempo máximo de espera exigido (Requisito 6.1).
bedrock_config = Config(
    read_timeout=TIMEOUT_SEGUNDOS,
    connect_timeout=TIMEOUT_SEGUNDOS,
    retries={"max_attempts": 0},
)

# Cria o cliente do serviço "bedrock-runtime" na região configurada (Requisito 5.1).
# As credenciais da AWS NÃO são escritas no código: o boto3 as resolve
# automaticamente a partir das variáveis de ambiente
# (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY e, quando aplicável,
# AWS_SESSION_TOKEN), conforme o Requisito 5.3.
client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=bedrock_config,
)

# ---------------------------------------------------------------------------
# Função auxiliar de geração de resposta
# ---------------------------------------------------------------------------


def gerar_resposta(mensagem):
    """Gera a resposta do KVN para uma mensagem do usuário usando o Bedrock.

    Recebe o texto da mensagem já validado pela rota e retorna o texto gerado
    pelo modelo Claude Haiku. Monta a requisição no formato da Messages API da
    Anthropic, chama o Bedrock e extrai o texto da resposta
    (Requisitos 4.2, 5.1, 5.2 e 2.3).

    Esta função também mantém a memória da conversa: antes de chamar o Bedrock,
    acrescenta a mensagem do usuário ao Historico_Conversa (Requisito 8.2) e
    envia TODO o histórico no campo `messages` (Requisito 8.3). Em caso de
    sucesso, acrescenta a resposta do KVN ao histórico (Requisito 8.4); em caso
    de falha, desfaz a inclusão da mensagem do usuário para preservar a
    alternância estrita de papéis (Requisito 8.5).
    """

    # Acrescenta a mensagem do usuário ao Historico_Conversa, no formato de
    # blocos de conteúdo de texto, ANTES de chamar o Bedrock (Requisito 8.2).
    # Guardamos a posição em que o item foi inserido para poder desfazer a
    # inclusão com segurança caso a geração falhe (Requisito 8.5).
    conversation_history.append(
        {"role": "user", "content": [{"type": "text", "text": mensagem}]}
    )

    # Monta o corpo da requisição no formato da Messages API da Anthropic.
    # - anthropic_version: versão fixa da API de mensagens da Anthropic no Bedrock.
    # - max_tokens: limite de tokens gerados na resposta.
    # - system: a SYSTEM_PROMPT vai no campo de sistema (Requisito 4.2), e não
    #   dentro de "messages".
    # - messages: TODO o Historico_Conversa, em ordem cronológica, para dar
    #   contexto ao modelo (Requisito 8.3). Como cada turno acrescenta uma
    #   mensagem do usuário e, em caso de sucesso, uma resposta do assistente,
    #   os papéis se alternam estritamente, começando e terminando em `user`.
    corpo = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": conversation_history,
    }

    # Tentamos chamar o Bedrock e processar a resposta. Se qualquer passo falhar
    # (erro de credenciais, erro do serviço, timeout ou formato inesperado da
    # resposta), desfazemos a inclusão da mensagem do usuário e re-lançamos a
    # exceção, para que o tratamento de erros da rota /chat continue valendo
    # sem alteração (Requisito 8.5).
    try:
        # Chama o modelo no Bedrock usando o MODEL_ID aprovado (Requisitos 5.1 e
        # 5.2). O corpo é serializado para JSON com json.dumps, e informamos que
        # o conteúdo enviado e aceito é "application/json".
        resposta = client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(corpo),
        )

        # A resposta do invoke_model traz o campo "body" como um stream.
        # Lemos o stream por completo e o interpretamos como JSON.
        dados = json.loads(resposta["body"].read())

        # Extrai o texto gerado. A resposta traz uma lista "content" com blocos
        # de texto; o texto do KVN está no primeiro bloco (Requisito 2.3).
        texto = dados["content"][0]["text"]
    except Exception:
        # A geração falhou (falha, erro ou timeout do Bedrock, ou resposta em
        # formato inesperado). Removemos do Historico_Conversa a mensagem do
        # usuário acrescentada no início deste turno, de modo que o histórico
        # volte exatamente ao estado anterior ao turno e a alternância estrita
        # de papéis seja mantida (Requisito 8.5). Como essa mensagem foi o
        # último item inserido e ainda não houve resposta do assistente, o
        # pop() sem índice remove exatamente esse item.
        conversation_history.pop()
        # Re-lança a exceção para que o tratamento de erros da rota /chat
        # (NoCredentialsError, ClientError, BotoCoreError, Exception) continue
        # funcionando sem alteração.
        raise

    # Sucesso: acrescenta a resposta do KVN ao Historico_Conversa com o papel
    # `assistant`, no mesmo formato de blocos de conteúdo de texto (Requisito 8.4).
    conversation_history.append(
        {"role": "assistant", "content": [{"type": "text", "text": texto}]}
    )

    # Devolve o texto gerado pelo KVN (Requisito 2.3).
    return texto

# ---------------------------------------------------------------------------
# Rota GET / (página de chat)
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Serve a página de chat do KVN.

    Renderiza o arquivo templates/index.html e o devolve ao navegador com
    status HTTP 200 (Requisito 1.1).

    Caso o template não seja encontrado ou não possa ser renderizado, a
    exceção é capturada e respondemos com status HTTP 500, indicando a falha
    ao carregar a página (Requisito 1.2). Isso mantém o servidor ativo e
    evita expor detalhes internos do erro ao usuário.
    """
    try:
        # Renderiza a página de chat. Por padrão, o Flask retorna status 200.
        return render_template("index.html")
    except Exception:
        # Qualquer falha ao localizar/renderizar o template resulta em uma
        # resposta HTTP 500 com uma indicação legível de que a página de chat
        # não pôde ser carregada (Requisito 1.2).
        return "Falha ao carregar a página de chat. Tente novamente.", 500

# ---------------------------------------------------------------------------
# Rota POST /chat (endpoint de conversa)
# ---------------------------------------------------------------------------

# Mensagem de erro de validação reutilizada nas respostas 400. Indica, de forma
# legível, que é obrigatório enviar uma mensagem não vazia de 1 a 2000 caracteres
# (Requisito 3.2). Usa a constante MAX_CHARS para manter o limite consistente.
ERRO_MENSAGEM_INVALIDA = (
    f"É obrigatório enviar uma mensagem não vazia (1 a {MAX_CHARS} caracteres)."
)

# Mensagem de erro usada quando as credenciais da AWS estão ausentes nas
# variáveis de ambiente (Requisito 5.4). Indica, de forma legível, que o serviço
# de IA está indisponível, sem expor qualquer detalhe de credencial.
ERRO_CREDENCIAIS = "Serviço de IA indisponível no momento. Tente novamente."

# Mensagem de erro usada quando ocorre uma falha, erro ou timeout na chamada ao
# Bedrock (Requisitos 6.1 e 6.2). Indica que a resposta não pôde ser gerada e
# que o usuário pode tentar novamente.
ERRO_BEDROCK = "Não foi possível gerar a resposta agora. Tente novamente."


@app.route("/chat", methods=["POST"])
def chat():
    """Recebe a mensagem do usuário e devolve a resposta do KVN.

    A rota primeiro VALIDA a entrada (Requisitos 3.1 e 3.2) e, para uma mensagem
    válida, chama o Bedrock via gerar_resposta e devolve o texto no campo `reply`
    com status 200 (Requisitos 2.1 e 2.3). Falhas de serviço são capturadas e
    convertidas em respostas HTTP 500 com `{"error": "..."}`, sem o campo `reply`
    e sem expor credenciais (Requisitos 5.4, 6.1, 6.2, 6.3), mantendo o servidor
    ativo para novas requisições (Requisito 6.4).

    A validação rejeita a requisição, com status HTTP 400 e corpo
    `{"error": "..."}`, quando:
      - o corpo não é um JSON válido / não contém um objeto JSON;
      - o campo `message` está ausente;
      - o campo `message` contém apenas espaços em branco (strip() vazio);
      - o campo `message` excede MAX_CHARS caracteres.
    Em todos esses casos o Bedrock NÃO é invocado (Requisito 3.1).
    """

    # Tenta ler o corpo da requisição como JSON. Usamos silent=True para que um
    # corpo não-JSON/ inválido resulte em None (em vez de levantar exceção), o
    # que também é tratado como entrada inválida com status 400.
    dados = request.get_json(silent=True)

    # Corpo ausente, não-JSON ou que não seja um objeto JSON (dicionário) é
    # considerado inválido: respondemos 400 sem invocar o Bedrock (Requisito 3.1).
    if not isinstance(dados, dict):
        return jsonify({"error": ERRO_MENSAGEM_INVALIDA}), 400

    # Extrai o campo `message` do corpo. Se estiver ausente, usa string vazia
    # como padrão para que a verificação de conteúdo a seguir o rejeite.
    mensagem = dados.get("message", "")

    # Garante que o valor seja uma string. Qualquer tipo diferente (número,
    # lista, etc.) é tratado como entrada inválida (Requisito 3.1).
    if not isinstance(mensagem, str):
        return jsonify({"error": ERRO_MENSAGEM_INVALIDA}), 400

    # Rejeita mensagem ausente/vazia ou composta apenas por espaços em branco:
    # strip() remove os espaços nas pontas; se o resultado for vazio, a mensagem
    # é inválida (Requisito 3.1). Também rejeita quando o tamanho excede MAX_CHARS.
    if not mensagem.strip() or len(mensagem) > MAX_CHARS:
        return jsonify({"error": ERRO_MENSAGEM_INVALIDA}), 400

    # Neste ponto a mensagem é válida. Geramos a resposta chamando o Bedrock e
    # tratamos as possíveis falhas de serviço para que o servidor permaneça
    # ativo após qualquer erro (Requisito 6.4).
    try:
        # Chama o Bedrock com a mensagem já validada e obtém o texto gerado pelo
        # KVN. Em caso de sucesso, devolvemos o texto no campo `reply` com
        # status 200 (Requisitos 2.1 e 2.3).
        texto = gerar_resposta(mensagem)
        return jsonify({"reply": texto}), 200

    except NoCredentialsError:
        # Credenciais da AWS ausentes nas variáveis de ambiente (Requisito 5.4).
        # Respondemos 500 com uma mensagem de indisponibilidade do serviço de IA,
        # SEM o campo `reply` e sem expor qualquer detalhe de credencial.
        return jsonify({"error": ERRO_CREDENCIAIS}), 500

    except (ClientError, BotoCoreError):
        # Qualquer falha, erro ou timeout na comunicação com o Bedrock
        # (Requisitos 6.1-6.3). BotoCoreError abrange também os timeouts
        # (ReadTimeoutError) e erros de conexão. Respondemos 500 com uma
        # mensagem legível pedindo nova tentativa, SEM o campo `reply`.
        return jsonify({"error": ERRO_BEDROCK}), 500

    except Exception:
        # Rede de segurança para qualquer outra falha inesperada ao gerar a
        # resposta (por exemplo, formato de resposta inesperado do Bedrock).
        # Capturamos aqui para que o servidor permaneça em execução e apto a
        # atender novas requisições (Requisito 6.4), respondendo 500 sem `reply`.
        return jsonify({"error": ERRO_BEDROCK}), 500

# ---------------------------------------------------------------------------
# Inicialização do servidor
# ---------------------------------------------------------------------------

# Este bloco só é executado quando o arquivo é rodado diretamente com
# `python app.py` (e não quando importado como módulo). Ele sobe o servidor
# Flask de desenvolvimento escutando em localhost na porta 5000 (Requisitos
# 1.5 e 7.3).
#
# Observação sobre a porta ocupada (Requisito 1.6): nenhum tratamento extra é
# necessário aqui. Se a porta 5000 já estiver em uso, o próprio servidor de
# desenvolvimento do Flask/Werkzeug falha ao fazer o bind e encerra a
# inicialização com uma indicação de porta indisponível (por padrão, um
# OSError do tipo "Address already in use"). Esse é o comportamento padrão
# esperado e suficiente para o projeto.
if __name__ == "__main__":
    # Inicia o servidor em localhost, na porta 5000 (Requisitos 1.5 e 7.3).
    app.run(host="localhost", port=5000)
