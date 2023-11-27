import requests
from bs4 import BeautifulSoup

def assitencia():
    try:
        url = "https://www.lance.com.br/tabela/brasileirao"
        response = requests.get(url)

        # Verificando se a requisição foi bem-sucedida (código 200)
        if response.status_code == 200:
            # Parseando o conteúdo HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Encontrando todas as divs que contêm as informações dos jogadores
            info_items = soup.find_all("div", class_="styles_infoItem__oVN6c")[:10]

            # Iterando sobre cada div para extrair os dados
            for item in info_items:
                ranking = item.find("div", class_="styles_infoPos__hzOKU").text.strip()
                team_name = item.find("img")["title"]
                player_name = item.find("span", class_="styles_playerName__iZPeZ").text
                position = item.find("span", class_="styles_playerPosition__T9BX1").text
                games = item.find_all("span")[0].text
                average = item.find_all("span")[1].text
                goals = item.find("p").text

                send_assitencia(ranking, team_name, player_name, position, games, average, goals)

        else:
            print("Failed to retrieve the page.")
    except requests.RequestException as e:
        print(f"Request Exception: {e}")

def send_assitencia(ranking, team_name, player_name, position, games, average, goals):
    try:
        message = "<b>Assistências do Brasileirão</b>\n\n"
        message += f"<b>Posição:</b> {ranking}\n"
        message += f"<b>Time:</b> {team_name}\n"
        message += f"<b>Jogador:</b> {player_name}\n"
        message += f"<b>Posição:</b> {position}\n"
        message += f"<b>Jogos:</b> {games}\n"
        message += f"<b>Média:</b> {average}\n"
        message += f"<b>Assistências:</b> {goals}\n"
        message += "-" * 30 + "\n"
                
        bot.send_message(CHANNEL, message)
        sleep(100)
    except Exception as e:
        print(f"Request Exception: {e}")
     