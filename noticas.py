import requests
from bs4 import BeautifulSoup

# URL da página
url = 'https://www.lance.com.br/mais-noticias.html'

# Fazendo a requisição HTTP
response = requests.get(url)

if response.status_code == 200:
    # Parseando o HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrando todos os cards de notícias
    cards = soup.find_all('div', class_='styles_card__XBZhk')
    
    # Iterando pelos cards e extraindo informações
    for card in cards:
        # Título da notícia
        title = card.find('h3').text.strip()
        
        # URL da notícia
        link = card.find('a')['href']
        
        # Data da notícia
        date = card.find('div', class_='styles_date__lZuoR').text.strip()
        
        # URL da imagem
        image = card.find('img')['src']
        
        print(f"Título: {title}")
        print(f"Link: {link}")
        print(f"Data: {date}")
        print(f"URL da Imagem: {image}")
        print("----------")
else:
    print("Falha ao obter a página")
