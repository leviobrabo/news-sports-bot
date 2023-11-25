import requests
from bs4 import BeautifulSoup

# Função para enviar a tabela como mensagem
def send_table_message():
    # Código para obter a tabela do Brasileirão Serie A
    response = requests.get('https://www.cnnbrasil.com.br/esportes/futebol/tabela-brasileirao-serie-a/')
    content = response.content
    site = BeautifulSoup(content, 'html.parser')

    tabela = site.find('tbody', class_='table__body')

    # Encontrando todas as linhas da tabela
    linhas = tabela.find_all('tr', class_='body__row')

    # Criando a mensagem formatada com a tabela
    message = "<b>Tabela Brasileirão Serie A:</b>\n\n"
    for linha in linhas:
        classificacao = linha.find('span').text.strip()
        nome_time = linha.find('span', class_='hide__s').text.strip()

        dados_time = linha.find_all('td')
        pontos = dados_time[2].text.strip()
        jogos = dados_time[3].text.strip()
        vitorias = dados_time[4].text.strip()
        empates = dados_time[5].text.strip()
        derrotas = dados_time[6].text.strip()
        saldo_gols = dados_time[7].text.strip()

        table_row = (
            f"<b>Posição:</b> {classificacao}\n"
            f"<b>Time:</b> {nome_time}\n"
            f"<b>Pontos:</b> {pontos}\n"
            f"<b>Jogos:</b> {jogos}\n"
            f"<b>Vitórias:</b> {vitorias}\n"
            f"<b>Empates:</b> {empates}\n"
            f"<b>Derrotas:</b> {derrotas}\n"
            f"<b>Saldo de Gols:</b> {saldo_gols}\n\n"
        )
        message += "━━━━━━━━━━━━━━━━━━"
        message += table_row

    # Enviar mensagem para o Telegram
    chat_id = bot.CHANNEL
    bot.send_message(chat_id, message)

# O código abaixo será executado apenas se este arquivo for executado diretamente
if __name__ == "__main__":
    send_table_message()