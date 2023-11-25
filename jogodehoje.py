import requests
from bs4 import BeautifulSoup

url = 'https://www.placardefutebol.com.br/jogos-de-hoje'

response = requests.get(url)

jogos_campeonato_brasileiro = []

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrando todos os containers de jogos do Campeonato Brasileiro da Série A
    containers = soup.find_all('div', class_='container content')

    for container in containers:
        # Verificando se o jogo é do Campeonato Brasileiro
        links_jogos = container.find_all('a', href=True)
        for link_jogo in links_jogos:
            link = link_jogo['href']
            if '/brasileirao-serie-a/' in link:
                # Encontrando o status do jogo
                status = link_jogo.find('span', class_='status-name').text.strip()

                # Encontrando os nomes dos times da casa e visitante
                team_home = link_jogo.find_all('h5', class_='team_link')[0].text.strip()
                team_away = link_jogo.find_all('h5', class_='team_link')[1].text.strip()

                # Extraindo o status do jogo (se está em andamento ou encerrado)
                if 'Encerrado' in status:
                    score_home = container.find_all('div', class_='match-score')[0].text.strip()
                    score_away = container.find_all('div', class_='match-score')[1].text.strip()
                    jogo = {
                        'Time da Casa': team_home,
                        'Placar Casa': score_home,
                        'Placar Visitante': score_away,
                        'Time Visitante': team_away,
                        'Status': status
                    }
                else:
                    jogo = {
                        'Time da Casa': team_home,
                        'Time Visitante': team_away,
                        'Status': status
                    }

                jogos_campeonato_brasileiro.append(jogo)

    # Exibindo todos os jogos do Campeonato Brasileiro da Série A
    for jogo in jogos_campeonato_brasileiro:
        if 'Placar Casa' in jogo:
            print(f"{jogo['Time da Casa']} {jogo['Placar Casa']} - {jogo['Placar Visitante']} {jogo['Time Visitante']} ({jogo['Status']})")
        else:
            print(f"{jogo['Time da Casa']} x {jogo['Time Visitante']} ({jogo['Status']})")
else:
    print("Não foi possível obter os dados.")
