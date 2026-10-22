# Plano de Implementação: KVN Chatbot

## Visão Geral

A implementação segue a stack obrigatória do steering: Python + Flask, com `app.py` na raiz e a interface em `templates/index.html`. O trabalho é dividido em passos incrementais que começam pela estrutura e pelas dependências, seguem para a configuração do Flask e a constante `SYSTEM_PROMPT`, a integração com o Amazon Bedrock via `boto3`, as rotas `/` e `/chat` com validação e tratamento de erros, e terminam com a interface de chat e a verificação manual.

Cada tarefa constrói sobre a anterior e termina integrando o código ao fluxo existente, sem deixar código órfão. Conforme o steering e o design, **não há tarefas de testes automatizados** — a verificação é feita manualmente seguindo o roteiro do documento de design.

## Tarefas

- [x] 1. Preparar estrutura e dependências do projeto
  - Criar o arquivo `requirements.txt` na raiz declarando `flask` e `boto3`
  - Criar a pasta `templates/` que abrigará a página de chat
  - Comentar o `requirements.txt` em português indicando o propósito de cada dependência
  - _Requisitos: 7.1, 7.2_

- [x] 2. Criar o esqueleto do `app.py` com Flask configurado
  - [x] 2.1 Criar `app.py` com a instância Flask e configuração de JSON
    - Importar `flask` e, na sequência, `boto3` (import que, ausente, encerra o processo indicando a dependência faltante)
    - Instanciar o app Flask e configurar `app.json.ensure_ascii = False` para preservar acentos legíveis
    - Comentar o código em português
    - _Requisitos: 2.2, 7.4_

  - [x] 2.2 Definir constantes de configuração em `app.py`
    - Definir `REGION = "us-east-1"`, `MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"`, `MAX_CHARS = 2000` e `TIMEOUT_SEGUNDOS = 30`
    - _Requisitos: 1.3, 3.1, 5.1, 5.2, 6.1_

- [x] 3. Definir a persona do KVN com a constante `SYSTEM_PROMPT`
  - Criar a constante `SYSTEM_PROMPT` em `app.py` com instruções explícitas de persona
  - Incluir: postura didática de professor para iniciantes com ao menos um exemplo quando aplicável; humor leve; escopo restrito a estudo de Inteligência Artificial; recusa educada e redirecionamento para temas de IA quando o pedido estiver fora de escopo
  - Comentar o bloco em português
  - _Requisitos: 4.1, 4.3, 4.4, 4.5_

- [x] 4. Configurar o cliente Bedrock e a função de geração de resposta
  - [x] 4.1 Criar o cliente `bedrock-runtime` do `boto3`
    - Criar o cliente na região `us-east-1` com `botocore.config.Config` definindo `read_timeout=30`, `connect_timeout=30` e `retries={"max_attempts": 0}` para garantir o limite de 30 segundos
    - Deixar as credenciais serem resolvidas automaticamente pelo `boto3` a partir das variáveis de ambiente, sem escrever chaves no código
    - _Requisitos: 5.1, 5.3, 6.1_

  - [x] 4.2 Implementar a função auxiliar `gerar_resposta(mensagem)`
    - Montar o corpo no formato da Messages API da Anthropic (`anthropic_version`, `max_tokens`, `system` com a `SYSTEM_PROMPT`, `messages` com a mensagem do usuário)
    - Chamar `client.invoke_model` com `modelId=MODEL_ID`, `contentType="application/json"`, `accept="application/json"` e `body=json.dumps(corpo)`
    - Ler o stream de resposta, fazer `json.loads` e extrair o texto de `content[0].text`
    - Comentar o código em português
    - _Requisitos: 4.2, 5.1, 5.2, 2.3_

- [x] 5. Implementar a rota `GET /`
  - Criar a rota `/` que renderiza `templates/index.html` e retorna status 200
  - Garantir que uma falha ao encontrar/renderizar o template resulte em resposta HTTP 500 indicando falha ao carregar a página
  - _Requisitos: 1.1, 1.2_

- [x] 6. Implementar a rota `POST /chat` com validação
  - [x] 6.1 Implementar a validação de entrada da mensagem
    - Ler o corpo JSON e extrair o campo `message`
    - Rejeitar quando `message` estiver ausente, for apenas espaços em branco (`strip()` vazio) ou exceder 2000 caracteres, retornando status 400 com `{"error": "..."}` e sem invocar o Bedrock
    - _Requisitos: 3.1, 3.2_

  - [x] 6.2 Implementar o fluxo de sucesso e o tratamento de erros de serviço
    - Para mensagem válida, chamar `gerar_resposta` e retornar `{"reply": "..."}` com status 200
    - Capturar ausência de credenciais e exceções do Bedrock (`ClientError`, `BotoCoreError`, `ReadTimeoutError`/timeout) retornando status 500 com `{"error": "..."}` legível, sem o campo `reply` e sem expor credenciais
    - Garantir que as exceções sejam capturadas na rota para que o servidor permaneça ativo após uma falha
    - _Requisitos: 2.1, 2.3, 5.4, 6.1, 6.2, 6.3, 6.4_

- [x] 7. Criar a interface de chat em `templates/index.html`
  - Criar a página com um campo de entrada de texto que aceite de 1 a 2000 caracteres e um controle de envio
  - Impedir o envio quando o campo estiver vazio (0 caracteres)
  - Implementar o envio via `fetch` para `POST /chat` com corpo `{"message": "..."}` e exibir o conteúdo de `reply` em caso de sucesso ou a mensagem de `error` em caso de falha
  - Comentar o código em português
  - _Requisitos: 1.3, 1.4, 2.1, 6.2_

- [x] 8. Finalizar a inicialização do servidor
  - Adicionar o bloco `if __name__ == "__main__":` em `app.py` para executar o servidor em `localhost` na porta `5000` ao rodar `python app.py`
  - Confirmar que o bind na porta 5000 ocupada encerra a inicialização com indicação de porta indisponível (comportamento padrão do servidor)
  - _Requisitos: 1.5, 1.6, 7.3_

- [x] 9. Checkpoint - Verificação manual
  - Executar a verificação manual conforme o roteiro da seção "Estratégia de Testes" do design (carregar a página, enviar mensagem válida sobre IA, conferir acentuação, mensagem vazia/longa, pedido fora de escopo, ausência de credenciais, falha do Bedrock, dependência ausente e porta ocupada)
  - Garantir que tudo funcione conforme esperado; perguntar ao usuário se surgirem dúvidas
  - _Requisitos: 1.1, 2.1, 2.2, 3.1, 4.5, 5.4, 6.1, 7.3_

## Notas

- Conforme o steering e o design, **nenhuma tarefa cria testes automatizados**; a verificação é manual (tarefa 9), seguindo o roteiro do documento de design.
- Cada tarefa referencia requisitos específicos para rastreabilidade.
- As tarefas são incrementais: estrutura → configuração → persona → integração → rotas → interface → inicialização, sem deixar código órfão.
- O código final é comentado em português, mantendo o projeto mínimo e didático.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2.1"] },
    { "id": 1, "tasks": ["2.2", "3"] },
    { "id": 2, "tasks": ["4.1"] },
    { "id": 3, "tasks": ["4.2", "5"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["6.2"] },
    { "id": 6, "tasks": ["7", "8"] }
  ]
}
```
