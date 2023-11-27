import requests
from bs4 import BeautifulSoup

def ultimos_jogos():
    try:
        url = 'https://www.lance.com.br/resenha-de-apostas/mais-noticias?page=1'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontrando todas as notícias
        all_news = soup.find_all('a', class_='')

        # Listas para armazenar os dados filtrados
        brasileirao_titles = []
        brasileirao_images = []
        brasileirao_dates = []
        brasileirao_links = []

        # Iterando por cada notícia
        for news in all_news:
            title = news.find('p', class_='text-more-news-title-desk-lg')
            image = news.find('img', class_='rounded-normal')
            date = news.find('p', class_='text-more-news-date-desk-lg')
            link = 'https://www.lance.com.br' + news['href']
            
            # Verificando se os elementos foram encontrados e se o título começa com "Brasileirão"
            if title and title.text.startswith('Brasileirão'):
                title_text = brasileirao_titles.append(title.text)
                image_url = brasileirao_images.append(image['src'])
                date_text = brasileirao_dates.append(date.text)
                link_text = brasileirao_links.append(link)

        # Imprimindo os dados filtrados
            send_photo_lance(title_text, image_url, date_text, link_text)

    except requests.RequestException as e:
        print(f"Request Exception: {e}")

def send_photo_lance(title_text, image_url, date_text, link_text):
    try:
        if db.search_title(title_text):
                    print(f"A notícia '{title_text}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title_text, date)

        button_text = f"https://www.lance.com.br{link_text}"  # Texto do botão
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(text='Ver notícia completa', url=button_text)
        markup.add(btn_news)
        
        bot.send_photo(CHANNEL, photo=image_url, caption=f"<b>{title_text}</b>\n\n<code>{date_text}</code>", reply_markup=markup)
        sleep(100)
    except Exception as e:
        print(f"Request Exception: {e}")
                