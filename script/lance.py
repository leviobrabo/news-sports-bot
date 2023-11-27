import requests
from bs4 import BeautifulSoup

def scrape_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            articles = soup.find_all('div', class_='styles_card__XBZhk')  # Altere essa classe de acordo com a estrutura do site

            for article in articles:
                title = article.find('h3').text.strip()
                image_url = article.find('img')['src']
                date = article.find('div', class_='styles_date__lZuoR').text.strip()

                # Verifica se o elemento do autor existe antes de tentar acessá-lo
                author_elem = article.find('span', style='color: var(--green-lance);')
                author = author_elem.text.strip() if author_elem else 'Autor não encontrado'

                link_elem = article.find('a')
                link = 'https://www.lance.com.br' + link_elem['href'] if link_elem else 'Link não encontrado'

                # Aqui você pode enviar os dados para o bot ou realizar alguma outra ação
                send_to_bot(title, image_url, date, author, link)

    except requests.RequestException as e:
        print(f"Request Exception: {e}")

def send_to_bot(title, image_url, date, author, link):
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
        
        bot.send_photo(CHANNEL, photo=image, caption=f"<b>{title}</b>\n\n<code>{date}</code>", reply_markup=markup)
        sleep(100)
    except Exception as e:
        print(f"Request Exception: {e}")
                

# Chame a função scrape_website com a URL do site desejado
scrape_website('https://www.lance.com.br/futebol-nacional/mais-noticias.html')
