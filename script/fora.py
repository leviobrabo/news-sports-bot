import requests
from bs4 import BeautifulSoup


def fora_do_campo():
    try:
        url = 'https://www.lance.com.br/fora-de-campo/mais-noticias.html'

        # Realizando a requisição GET
        response = requests.get(url)

        if response.status_code == 200:
            # Parsing do HTML com BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrando a lista de notícias
            news_list = soup.find('ul', class_='styles_list__7maJJ')

            if news_list:
                # Iterando sobre cada item de notícia na lista
                for news_item in news_list.find_all('li'):
                    # Obtendo o título da notícia
                    title = news_item.find('h3').text.strip()

                    # Obtendo a URL da imagem
                    image_url = 'https://www.lance.com.br' + news_item.find('img')['src']

                    # Obtendo o horário e a data da notícia
                    datetime = news_item.find('div', class_='styles_date__lZuoR').text.strip()

                    # Obtendo o link da notícia
                    link = news_item.find('a')['href']

                    # Obtendo o autor, se estiver disponível
                    author = news_item.find('span', style='color:var(--green-lance)')
                    author_name = author.text if author else 'Autor não disponível'

                    # Imprimindo os dados coletados
                    send_text_fora_do_campo(title, image_url, datetime, author_name, link)

            else:
                print("Lista de notícias não encontrada.")
        else:
            print("Falha ao obter a página.")
    except requests.RequestException as e:
            print(f"Request Exception: {e}")

def send_text_fora_do_campo(title, image_url, datetime, author_name, link):
    try:
        if db.search_title(title):
                    print(f"A notícia '{title}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title, date)

        button_text = f"https://www.lance.com.br{link}"  # Texto do botão
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(text='Ver notícia completa', url=button_text)
        markup.add(btn_news)
        
        bot.send_photo(CHANNEL, photo=image_url, caption=f"<b>{title}</b>\n\n<code>{datetime}</code> - Feito por {author_name}", reply_markup=markup)
        sleep(100)
    except Exception as e:
        print(f"Request Exception: {e}")
          