# Documento de Requisitos

## Introdução

O KVN é um chatbot educacional voltado a ajudar o usuário a estudar conteúdos de Inteligência Artificial. O KVN adota uma postura de professor, com didática clara e humor leve, respondendo às perguntas do usuário em uma interface web simples de chat.

A aplicação é construída em Python com Flask, expõe uma página de chat e um endpoint que recebe mensagens e devolve respostas geradas pelo Amazon Bedrock (modelo Claude Haiku) por meio da biblioteca boto3. O projeto é mínimo e didático, com poucos arquivos e código comentado em português.

## Glossário

- **KVN**: Nome do chatbot educacional que atua como professor com humor leve, objeto deste documento.
- **Aplicacao_Flask**: Servidor web em Python com Flask, composto por `app.py` na raiz e a página `templates/index.html`.
- **Pagina_Chat**: Página HTML servida pela rota `/` que apresenta a interface de conversa ao usuário.
- **Endpoint_Chat**: Rota `/chat` que aceita requisições HTTP POST com um corpo JSON contendo o campo `message`.
- **Servico_Bedrock**: Cliente `bedrock-runtime` do Amazon Bedrock acessado via boto3 na região `us-east-1`, usado para gerar respostas.
- **SYSTEM_PROMPT**: Constante definida em `app.py` que descreve a personalidade, o tom e os limites de atuação do KVN.
- **Model_ID**: Identificador do modelo de inferência utilizado: `us.anthropic.claude-haiku-4-5-20251001-v1:0`.
- **Usuario**: Pessoa que estuda conteúdos de IA e interage com o KVN pela Pagina_Chat.
- **Mensagem**: Texto enviado pelo Usuario ao Endpoint_Chat no campo `message` do corpo JSON.
- **Resposta**: Texto gerado pelo Servico_Bedrock e devolvido ao Usuario no campo `reply` do corpo JSON.
- **Historico_Conversa**: Lista Python definida em nível de módulo em `app.py` que armazena, em ordem cronológica, as Mensagens do Usuario e as Respostas do KVN trocadas durante a execução da Aplicacao_Flask.
- **Turno**: Par composto por uma Mensagem do Usuario e a Resposta correspondente do KVN, registrado no Historico_Conversa.

## Requisitos

### Requisito 1: Servir a página de chat

**User Story:** Como Usuario, quero acessar uma página de chat no navegador, para que eu possa conversar com o KVN sobre conteúdos de IA.

#### Acceptance Criteria

1. WHEN o Usuario acessa a rota `/` via HTTP GET, THE Aplicacao_Flask SHALL retornar a Pagina_Chat renderizada a partir de `templates/index.html` com status HTTP 200 em até 2 segundos.
2. IF o arquivo `templates/index.html` não for encontrado ou não puder ser renderizado, THEN THE Aplicacao_Flask SHALL retornar status HTTP 500 com uma indicação de erro informando a falha ao carregar a Pagina_Chat.
3. THE Pagina_Chat SHALL apresentar um campo de entrada de texto para a Mensagem que aceite entre 1 e 2000 caracteres.
4. THE Pagina_Chat SHALL apresentar um controle de envio que, quando acionado sem texto na Mensagem (0 caracteres), não dispare o envio.
5. WHEN a Aplicacao_Flask é iniciada com `python app.py`, THE Aplicacao_Flask SHALL escutar em `localhost` na porta `5000`.
6. IF a porta `5000` já estiver em uso no momento da inicialização, THEN THE Aplicacao_Flask SHALL encerrar a inicialização e retornar uma indicação de erro informando que a porta está indisponível.

### Requisito 2: Receber mensagem e devolver resposta

**User Story:** Como Usuario, quero enviar uma mensagem de estudo e receber uma resposta do KVN, para que eu possa aprender conteúdos de IA.

#### Acceptance Criteria

1. WHEN o Endpoint_Chat recebe uma requisição HTTP POST contendo um corpo JSON com o campo `message` preenchido com um texto de 1 a 2000 caracteres, THE Aplicacao_Flask SHALL encaminhar o conteúdo da Mensagem ao Servico_Bedrock e retornar a Resposta no campo `reply` de um corpo JSON com status 200.
2. THE Aplicacao_Flask SHALL configurar `app.json.ensure_ascii` como `False` para que a Resposta preserve acentos legíveis no JSON.
3. WHEN o Servico_Bedrock gera a Resposta, THE Aplicacao_Flask SHALL incluir o conteúdo textual da Resposta no campo `reply` do corpo JSON retornado.

### Requisito 3: Validar mensagem vazia

**User Story:** Como Usuario, quero receber um retorno claro quando enviar uma mensagem vazia, para que eu entenda que preciso digitar algo antes de enviar.

#### Acceptance Criteria

1. IF o Endpoint_Chat recebe uma requisição POST cujo campo `message` está ausente, contém apenas espaços em branco, ou excede 2000 caracteres, THEN THE Aplicacao_Flask SHALL retornar uma resposta de erro com status 400 e NÃO SHALL invocar o Servico_Bedrock.
2. WHEN a Aplicacao_Flask retorna o erro 400 por Mensagem inválida, THE Aplicacao_Flask SHALL incluir no corpo JSON uma descrição textual indicando que uma Mensagem não vazia é obrigatória.

### Requisito 4: Personalidade do KVN

**User Story:** Como Usuario, quero que o KVN responda como um professor com humor leve, para que o estudo de IA seja claro e agradável.

#### Acceptance Criteria

1. THE Aplicacao_Flask SHALL definir a personalidade, o tom e o escopo de atuação do KVN em uma constante SYSTEM_PROMPT em `app.py`, incluindo instruções explícitas para: (a) adotar postura didática de professor, (b) incluir humor leve, e (c) restringir as respostas a temas de estudo de Inteligência Artificial.
2. WHEN a Aplicacao_Flask solicita a geração de uma Resposta ao Servico_Bedrock, THE Aplicacao_Flask SHALL enviar a SYSTEM_PROMPT como instrução de sistema da requisição.
3. THE SYSTEM_PROMPT SHALL instruir o KVN a estruturar cada Resposta de forma didática, apresentando ao menos uma explicação do conceito solicitado e, quando aplicável, um exemplo, mantendo linguagem acessível a estudantes iniciantes em IA.
4. WHEN a Mensagem do Usuario solicita conteúdo relacionado a estudo de Inteligência Artificial, THE SYSTEM_PROMPT SHALL instruir o KVN a responder ao conteúdo solicitado incluindo um comentário de humor leve.
5. IF a Mensagem do Usuario solicita conteúdo não relacionado a estudo de Inteligência Artificial, THEN THE SYSTEM_PROMPT SHALL instruir o KVN a recusar a solicitação e redirecionar o Usuario para temas de estudo de IA, sem fornecer o conteúdo fora de escopo.

### Requisito 5: Integração com o Amazon Bedrock

**User Story:** Como Usuario, quero que as respostas venham do Amazon Bedrock com o modelo definido, para que o KVN utilize exclusivamente o provedor de IA aprovado no projeto.

#### Acceptance Criteria

1. WHEN o Endpoint_Chat recebe uma Mensagem válida, THE Aplicacao_Flask SHALL gerar a Resposta chamando o método `invoke_model` do Servico_Bedrock `bedrock-runtime` na região `us-east-1`.
2. THE Aplicacao_Flask SHALL utilizar o Model_ID `us.anthropic.claude-haiku-4-5-20251001-v1:0` em todas as chamadas ao Servico_Bedrock.
3. THE Aplicacao_Flask SHALL obter as credenciais de acesso à AWS exclusivamente a partir de variáveis de ambiente.
4. IF as credenciais de acesso à AWS não estiverem presentes nas variáveis de ambiente no momento da chamada, THEN THE Aplicacao_Flask SHALL abortar a geração da Resposta e retornar ao Usuario uma mensagem de erro indicando indisponibilidade do serviço de IA, sem expor as credenciais.

### Requisito 6: Tratamento de falhas do serviço de IA

**User Story:** Como Usuario, quero receber um retorno compreensível quando a geração de resposta falhar, para que eu saiba que ocorreu um problema e possa tentar novamente.

#### Acceptance Criteria

1. IF a chamada ao Servico_Bedrock falha, retorna um erro ou não é concluída dentro de 30 segundos, THEN THE Aplicacao_Flask SHALL retornar uma resposta de erro com status 500.
2. WHEN a Aplicacao_Flask retorna o erro 500 por falha do Servico_Bedrock, THE Aplicacao_Flask SHALL incluir no corpo JSON uma mensagem textual legível indicando que a geração da Resposta falhou e que o Usuario pode tentar novamente.
3. WHEN a Aplicacao_Flask retorna o erro 500 por falha do Servico_Bedrock, THE Aplicacao_Flask SHALL omitir o campo `reply` do corpo JSON, de modo que a resposta de erro seja distinguível de uma resposta bem-sucedida.
4. IF ocorre uma falha do Servico_Bedrock, THEN THE Aplicacao_Flask SHALL permanecer em execução e continuar apta a atender novas requisições ao Endpoint_Chat.

### Requisito 7: Dependências e execução do projeto

**User Story:** Como desenvolvedor, quero declarar as dependências e um modo de execução simples, para que eu consiga instalar e rodar o KVN com poucos passos.

#### Acceptance Criteria

1. THE Aplicacao_Flask SHALL declarar as dependências `flask` e `boto3` em um arquivo `requirements.txt`.
2. THE Aplicacao_Flask SHALL ser estruturada com `app.py` na raiz do projeto e a Pagina_Chat em `templates/index.html`.
3. WHEN o comando `python app.py` é executado com as dependências instaladas, THE Aplicacao_Flask SHALL iniciar um servidor web local que passa a aceitar requisições HTTP e disponibiliza a Pagina_Chat, em até 10 segundos.
4. IF o comando `python app.py` é executado sem as dependências `flask` ou `boto3` instaladas, THEN THE Aplicacao_Flask SHALL encerrar a execução sem iniciar o servidor e exibir uma mensagem de erro indicando qual dependência está ausente.

### Requisito 8: Memória de conversa

**User Story:** Como Usuario, quero que o KVN lembre das mensagens anteriores da conversa, para que eu possa fazer perguntas de acompanhamento sem repetir o contexto a cada vez.

#### Acceptance Criteria

1. THE Aplicacao_Flask SHALL manter o Historico_Conversa como uma lista Python em nível de módulo em `app.py`, inicializada vazia quando a Aplicacao_Flask é iniciada.
2. WHEN o Endpoint_Chat recebe uma Mensagem válida, THE Aplicacao_Flask SHALL acrescentar a Mensagem do Usuario ao Historico_Conversa com o papel `user` antes de solicitar a geração da Resposta ao Servico_Bedrock.
3. WHEN a Aplicacao_Flask solicita a geração de uma Resposta ao Servico_Bedrock, THE Aplicacao_Flask SHALL incluir no campo `messages` da requisição todas as Mensagens do Usuario e Respostas do KVN presentes no Historico_Conversa, em ordem cronológica, de modo que os papéis se alternem estritamente iniciando em `user` e terminando em `user`, sem dois papéis iguais consecutivos.
4. WHEN o Servico_Bedrock gera uma Resposta com sucesso, THE Aplicacao_Flask SHALL acrescentar a Resposta do KVN ao Historico_Conversa com o papel `assistant`.
5. IF a geração da Resposta pelo Servico_Bedrock falha, retorna erro ou não é concluída dentro de 30 segundos, THEN THE Aplicacao_Flask SHALL remover do Historico_Conversa a Mensagem do Usuario acrescentada no turno em andamento e NÃO SHALL acrescentar Resposta alguma do KVN para esse turno, de modo que o Historico_Conversa retorne ao mesmo estado anterior ao início do turno e mantenha a alternância estrita de papéis `user` e `assistant`.
6. THE Aplicacao_Flask SHALL preservar o Historico_Conversa entre requisições sucessivas ao Endpoint_Chat durante a mesma execução do servidor.
