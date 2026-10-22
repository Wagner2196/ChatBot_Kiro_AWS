# KVN — Seu Professor de Inteligência Artificial

KVN é um chatbot educacional que atua como um professor de IA, com didática clara e humor leve. Ele é servido por uma interface web de chat e suas respostas são geradas pelo Amazon Bedrock. Seu escopo é restrito ao estudo de Inteligência Artificial: quando o pedido foge desse tema, o KVN recusa de forma educada e convida a pessoa a voltar para assuntos de IA.

## Funcionalidades

- Interface web de chat (página servida em `GET /` e envio de mensagens via `POST /chat`).
- Persona de professor de IA, com explicações para iniciantes e humor leve.
- Escopo restrito ao estudo de Inteligência Artificial, com recusa educada fora de escopo.
- Validação de mensagem: texto não vazio de 1 a 2000 caracteres.
- Memória de conversa durante a execução do servidor (o histórico é enviado ao modelo a cada turno).
- Tratamento de erros (credenciais ausentes, falhas e timeouts do Bedrock) sem derrubar o servidor.

## Tecnologias

- Python
- Flask
- boto3
- Amazon Bedrock (Claude Haiku 4.5)
  - Modelo: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  - Região: `us-east-1`

## Contexto

Criado no II Workshop de Ciência da Computação da UNIFAL-MG, outubro de 2026.

## Como executar

1. Clone o repositório

   ```bash
   git clone <URL-DO-REPOSITORIO>
   cd Aula2Kiro
   ```

2. Instale as dependências

   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente AWS (requer credenciais próprias)

   Linux / macOS:

   ```bash
   export AWS_ACCESS_KEY_ID=<SUA_ACCESS_KEY_ID>
   export AWS_SECRET_ACCESS_KEY=<SUA_SECRET_ACCESS_KEY>
   # Opcional (quando usar credenciais temporárias):
   export AWS_SESSION_TOKEN=<SEU_SESSION_TOKEN>
   ```

   Windows (PowerShell):

   ```powershell
   $env:AWS_ACCESS_KEY_ID = "<SUA_ACCESS_KEY_ID>"
   $env:AWS_SECRET_ACCESS_KEY = "<SUA_SECRET_ACCESS_KEY>"
   # Opcional (quando usar credenciais temporárias):
   $env:AWS_SESSION_TOKEN = "<SEU_SESSION_TOKEN>"
   ```

4. Inicie a aplicação

   ```bash
   python app.py
   ```

   (Em alguns ambientes Linux, o interpretador é `python3`.)

5. Acesse http://127.0.0.1:5000

> **Nota:** Requer uma conta AWS com acesso ao Amazon Bedrock habilitado (modelo Claude Haiku na região us-east-1).

## API

- `GET /` — serve a página de chat (`templates/index.html`).
- `POST /chat` — recebe `{"message": "..."}` e responde `{"reply": "..."}` com status 200.
  - Mensagem inválida (ausente, vazia ou acima de 2000 caracteres): status 400 com `{"error": "..."}`.
  - Falha de serviço (credenciais ausentes, erro ou timeout do Bedrock): status 500 com `{"error": "..."}`.

## Estrutura do projeto

```text
Aula2Kiro/
├── app.py              # Aplicação Flask: rotas e integração com o Amazon Bedrock
├── templates/
│   └── index.html      # Interface web de chat
├── requirements.txt    # Dependências (Flask, boto3)
├── .gitignore
├── README.md
└── .kiro/              # Artefatos do Kiro (specs, steering)
```

## Demonstração

https://github.com/Wagner2196/ChatBot_Kiro_AWS/issues/1
