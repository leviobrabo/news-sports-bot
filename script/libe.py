import requests
from bs4 import BeautifulSoup


def libertadores():
    try:
        url = 'https://www.lance.com.br/libertadores/mais-noticias.html'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            posts = soup.find_all('div', class_='styles_card__XBZhk')

            for post in posts:
                title = post.find('h3').text.strip()
                image_url = post.find('img')['src']
                date_time = post.find('div', class_='styles_date__lZuoR').text.strip()
                author_tag = post.find('span', style='color:var(--green-lance)')
                if author_tag:
                    author = author_tag.text.strip()
                else:
                    # If not found, try to find another pattern or skip
                    # For instance, if the author is within a different structure
                    author = "Author Not Found"  # Modify this accordingly
                post_url = 'https://www.lance.com.br' + post.find('a')['href']

                send_libertadores_text(title, image_url, date_time, author, post_url)
        else:
            print("Failed to retrieve the webpage")
    except requests.RequestException as e:
        logger.info(f"Request Exception: {e}")

def send_libertadores_text(title, image_url, date_time, author, post_url):
    try:
        if db.search_title(title):
                    logger.info(f"A notícia '{title}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title, date)

        button_text = f"https://www.lance.com.br{post_url}"  # Texto do botão
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(text='Ver notícia completa', url=button_text)
        markup.add(btn_news)
        
        bot.send_photo(CHANNEL, photo=image_url, caption=f"<b>{title}</b>\n\n<code>{date_time}</code> - Feito por: {author}", reply_markup=markup)
        sleep(100)
    except Exception as e:
        logger.info(f"Request Exception: {e}")