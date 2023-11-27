import requests
from bs4 import BeautifulSoup


def artilheiro_py():
    try:

        url = "https://www.lance.com.br/tabela/brasileirao"

        # Fazendo uma requisição GET para obter o conteúdo HTML da página
        response = requests.get(url)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Parsing do conteúdo HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Encontrando todos os elementos com a classe 'styles_infoItem__oVN6c' que contêm informações dos artilheiros
            artilheiros = soup.find_all(class_="styles_infoItem__oVN6c")[:10]

            # Iterando pelos artilheiros e extraindo as informações desejadas
            for artilheiro in artilheiros:
                posicao = artilheiro.find(class_="styles_infoPos__hzOKU").text.strip()
                nome_time = artilheiro.find(title=True)['title']
                nome_jogador = artilheiro.find(class_="styles_playerName__iZPeZ").text.strip()
                posicao_jogador = artilheiro.find(class_="styles_playerPosition__T9BX1").text.strip()
                jogos = artilheiro.find_all("span")[0].text.strip()
                media = artilheiro.find_all("span")[1].text.strip()
                gols = artilheiro.find("p").text.strip()

                send_artilheiro(posicao, nome_time, nome_jogador, posicao_jogador, jogos, media, gols)
        else:
            print("Falha ao obter a página")
    except requests.RequestException as e:
        print(f"Request Exception: {e}")

def send_artilheiro(posicao, nome_time, nome_jogador, posicao_jogador, jogos, media, gols):
    try:
        message = "<b>Artilheiros do Brasileirão</b>\n\n"
        message += f"<b>Posição:</b> {posicao}\n"
        message += f"<b>Time:</b> {nome_time}\n"
        message += f"<b>Jogador:</b> {nome_jogador}\n"
        message += f"<b>Posição:</b> {posicao_jogador}\n"
        message += f"<b>Jogos:</b> {jogos}\n"
        message += f"<b>Média:</b> {media}\n"
        message += f"<b>Gols:</b> {gols}\n"
        message += "-" * 30 + "\n"
                
        bot.send_message(CHANNEL, message)
        sleep(100)
    except Exception as e:
        print(f"Request Exception: {e}")
