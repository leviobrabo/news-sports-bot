# news-sports

Este é um bot Telegram personalizado para fornecer notícias de futebol e outras informações relevantes sobre esportes. Ele possui funcionalidades para raspagem de notícias, criação de posts no Telegraph e envio de informações relevantes para os usuários.

### Variáveis de Ambiente

Para o funcionamento correto do bot, é necessário configurar as seguintes variáveis de ambiente:

#### Variáveis de Log

-   `LOG_PATH`: Caminho para o arquivo de log do bot.

#### Variáveis de Notícias

-   `TOKEN`: Token de autenticação do bot Telegram.
-   `NEWS_LOG`: ID do log de notícias.
-   `NEWS_CHANNEL`: ID do canal de notícias.
-   `CHANNEL_USERNAME`: Nome do canal de notícias.
-   `BOT_NAME`: Nome do bot Telegram.
-   `BOT_USERNAME`: Nome de usuário do bot Telegram.
-   `OWNER_ID`: ID do proprietário do bot.
-   `OWNER_USERNAME`: Nome de usuário do proprietário do bot.
-   `TELEGRAPH_TOKEN`: Token do Telegraph para criação de posts.

#### Variáveis de Banco de Dados

-   `MONGO_CON`: String de conexão MongoDB.

Certifique-se de configurar corretamente estas variáveis de ambiente antes de executar o bot.

### Configuração das Variáveis de Ambiente

1. Crie um arquivo `bot.conf` na raiz do projeto:

````plaintext
  [LOG]
  LOG_PATH=/caminho/para/o/arquivo/de/log.log

  [NEWS]
  TOKEN=SEU_TOKEN_AQUI
  NEWS_LOG=ID_DO_LOG_DE_NOTÍCIAS
  NEWS_CHANNEL=ID_DO_CANAL_DE_NOTÍCIAS
  CHANNEL_USERNAME=NOME_DO_CANAL
  BOT_NAME=NOME_DO_BOT
  BOT_USERNAME=USERNAME_DO_BOT
  OWNER_ID=ID_DO_PROPRIETÁRIO
  OWNER_USERNAME=USERNAME_DO_PROPRIETÁRIO
  TELEGRAPH_TOKEN=SEU_TOKEN_DO_TELEGRAPH

  [DB]
  MONGO_CON=SUA_STRING_DE_CONEXÃO_MONGO

Certifique-se de configurar o arquivo bot.conf com as variáveis de ambiente necessárias.

```bash
cp sample.bot.conf bot.conf
````

## Configuração e Execução

2. **Instalação de Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Execução do Bot:

Execute o arquivo principal bot.py para iniciar o bot:

```bash
  python  main.py
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para fazer fork deste repositório, adicionar novos recursos, corrigir bugs e enviar um pull request.

[PR](https://github.com/leviobrabo/news-sports-bot/pulls)

## Observações Importantes

-   Este projeto é destinado apenas como exemplo e pode ser modificado e adaptado conforme suas necessidades.
-   Certifique-se de seguir as diretrizes de segurança ao lidar com chaves de API e informações sensíveis.
-   Verifique a documentação do Telegram para entender melhor sobre a API e suas funcionalidades.
