# news-sports

Este é um bot Telegram personalizado para fornecer notícias de futebol e outras informações relevantes sobre esportes. Ele possui funcionalidades para raspagem de notícias, criação de posts no Telegraph e envio de informações relevantes para os usuários.

## Variáveis de Ambiente

Para o funcionamento correto do bot, é necessário configurar as seguintes variáveis de ambiente:

-   `TELEGRAPH_API_KEY`: Chave de API do Telegraph para criar posts.
-   `BOT_TOKEN`: Token de autenticação do bot Telegram.
-   `CHANNEL_ID`: ID do canal Telegram onde as notícias serão enviadas.
-   Outras variáveis específicas para sua aplicação, como chaves de API de serviços externos, se necessário.

Certifique-se de configurar corretamente estas variáveis de ambiente antes de executar o bot.

## Configuração e Execução

1. **Instalação de Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuração das Variáveis de Ambiente:

Certifique-se de configurar o arquivo bot.conf com as variáveis de ambiente necessárias.

```bash
cp sample.bot.conf bot.conf
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
