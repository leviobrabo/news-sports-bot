import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

import configparser

import telebot
from telebot import types
import telegraph

from datetime import datetime, timedelta
from time import sleep

import os
import io
import schedule
import db
from loguru import logger

import news.artilheiro
import news.tabela

config = configparser.ConfigParser()
config.read('bot.conf')
logger.add(config['LOG']['LOG_PATH'])

TOKEN = config['NEWS']['TOKEN']
GROUP_LOG = int(config['NEWS']['NEWS_LOG'])
CHANNEL = int(config['NEWS']['NEWS_CHANNEL'])
CHANNEL_USERNAME = config['NEWS']['CHANNEL_USERNAME']
OWNER = int(config['NEWS']['OWNER_ID'])
TELEGRAPH = config['NEWS']['TELEGRAPH_TOKEN']

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')


def get_news(limit=5):
    try:
        logger.info('Obtendo notícias...')
        url = 'https://ge.globo.com/futebol/brasileirao-serie-a/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        post_sections = soup.find_all('div', {'class': 'bastian-feed-item'})

        news_list = []
        for section in post_sections[:limit]:
            logger.info('Notícia recebida')
            title_element = section.find('a', {'class': 'feed-post-link'})
            description_element = section.find(
                'div', {'class': 'feed-post-body-resumo'}
            )
            link_element = section.find('a', {'class': 'feed-post-link'})
            image_element = section.find(
                'img', {'class': 'bstn-fd-picture-image'}
            )

            if link_element:
                link_response = requests.get(
                    link_element['href'], timeout=10, headers=headers
                )
                link_content = BeautifulSoup(
                    link_response.content, 'html.parser'
                )

                full_text_content = link_content.find_all(
                    'div',
                    {'class': 'mc-column content-text active-extra-styles'},
                )
                media_content = link_content.find_all(
                    'div', {'class': 'mc-column content-media__container'}
                )

                full_text = ''
                media_links = []
                for text_section in full_text_content:
                    text = text_section.get_text(strip=True)
                    if text:
                        full_text += text + '\n\n'

                for media_section in media_content:
                    media_element = media_section.find('img')
                    if media_element and 'src' in media_element.attrs:
                        media_links.append(media_element['src'])
                        if 'src' in media_element.attrs:
                            image_url = media_element['src']
                        else:
                            image_url = None

                        full_text += f'<img src="{image_url}">\n\n'

                autor_element = link_content.find(
                    'p', {'class': 'content-publication-data__from'}
                )

                if (
                    title_element
                    and link_element
                    and description_element
                    and image_element
                ):
                    title = title_element.text.strip()
                    link = link_element['href']
                    description = description_element.text.strip()

                    if autor_element:
                        autor = autor_element.text
                    else:
                        autor = None

                    news_list.append(
                        {
                            'title': title,
                            'description': description,
                            'link': link,
                            'image': image_url
                            if 'image_url' in locals()
                            else None,
                            'autor': autor,
                            'full_text': full_text,
                            'media_links': media_links,
                        }
                    )
                    if len(news_list) >= limit:
                        break

        logger.info(f'{len(news_list)} notícias obtidas.')
        return news_list
    except Exception as e:
        logger.exception(f'Erro ao obter notícias: {str(e)}')
        return []


def upload_telegraph_image(image_url, attempt=0):
    logger.info('Fazendo upload da imagem no Telegraph...')
    if attempt == 3:
        return None

    telegraph_api = telegraph.Telegraph(TELEGRAPH)

    try:
        file = requests.get(image_url)
        if file.status_code != 200:
            logger.warning(f'Erro ao baixar imagem do link: {image_url}')
            return None

        inmemoryfile = io.BytesIO(file.content)
        path = telegraph_api.upload_file(inmemoryfile)
        return f'https://telegra.ph{path[0]["src"]}' if path else None

    except Exception as e:
        logger.exception(
            f'Erro ao fazer upload da imagem no Telegraph: {str(e)}'
        )
        return None


def create_telegraph_post(
    title, description, link, image_url, autor, full_text
):
    logger.info('Criando post no Telegraph...')
    try:
        telegraph_api = telegraph.Telegraph(TELEGRAPH)

        paragraphs = [
            f'<p>{paragraph}</p>' for paragraph in full_text.split('\n\n')
        ]
        formatted_text = ''.join(paragraphs)

        response = telegraph_api.create_page(
            f'{title}',
            html_content=(
                f'<img src="{image_url}"><br><br>'
                + f'<h4>{description}</h4><br><br>'
                + f'<p>{formatted_text}</p><br><br>'
                + f'<a href="{link}">Leia a matéria original</a>'
            ),
            author_name=f'{autor}',
        )
        return response['url'], title, link

    except Exception as e:
        logger.exception(f'Erro ao criar post no Telegraph: {str(e)}')
        return None, None, None


def create_telegraph_posts():
    logger.info('Criando posts no Telegraph...')
    news = get_news()
    telegraph_links = []

    for n in news:
        title = n['title']
        description = n['description']
        link = n['link']
        image_url = n['image']
        autor = n['autor']
        full_text = n['full_text']

        telegraph_link = create_telegraph_post(
            title, description, link, image_url, autor, full_text
        )
        if telegraph_link[0]:
            telegraph_links.append(telegraph_link)

    logger.info(f'{len(telegraph_links)} posts criados no Telegraph.')
    return telegraph_links


def send_news_g1():
    try:
        logger.info('Iniciando verificação e envio de notícias...')
        created_links = create_telegraph_posts()

        for telegraph_link, title, original_link in created_links:
            news_name = db.search_title(title)

            if news_name:
                logger.info('A notícia já foi postada.')
            else:
                logger.info('Adicionando notícia ao banco de dados...')
                current_datetime = datetime.now() - timedelta(hours=3)
                date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
                db.add_news(title, date)

                logger.info('Enviando notícia...')
                bot.send_message(
                    CHANNEL,
                    f'<a href="{telegraph_link}">󠀠</a><b>{title}</b>\n\n'
                    f'🗞 <a href="{original_link}">G1 SPORTS</a>',
                    parse_mode='HTML',
                )
                sleep(300)
    except Exception as e:
        logger.exception(
            f'Erro durante verificação e envio de notícias: {str(e)}'
        )


def total_news():
    try:
        all_news = db.get_all_news()
        total_count = len(list(all_news))
        bot.send_message(
            GROUP_LOG,
            f'TOTAL de Notícia enviada hoje: <code>{total_count}</code> Notícias',
            message_thread_id=38593,
        )
    except Exception as e:
        logger.exception(f'Error sending total news count: {str(e)}')


def delete_news():
    try:
        logger.info('Deletando todas as noticias do bnaco de dados...')
        db.remove_all_news()
    except Exception as e:
        logger.exception(
            f'Erro ao deletar as notícias do banco de dados: {str(e)}'
        )



def placar_de_jogo():
    url = 'https://www.placardefutebol.com.br/jogos-de-hoje'

    response = requests.get(url)

    jogos_campeonato_brasileiro = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        containers = soup.find_all('div', class_='container content')

        for container in containers:
            links_jogos = container.find_all('a', href=True)
            for link_jogo in links_jogos:
                link = link_jogo['href']
                if '/brasileirao-serie-a/' in link:
                    status = link_jogo.find('span', class_='status-name').text.strip()

                    team_home = link_jogo.find_all('h5', class_='team_link')[0].text.strip()
                    team_away = link_jogo.find_all('h5', class_='team_link')[1].text.strip()

                    if 'Encerrado' in status:
                        score_home = container.find_all('div', class_='match-score')[0].text.strip()
                        score_away = container.find_all('div', class_='match-score')[1].text.strip()
                        jogo = {
                            'Time da Casa': team_home,
                            'Placar Casa': score_home,
                            'Placar Visitante': score_away,
                            'Time Visitante': team_away,
                            'Status': status,
                        }
                    else:
                        jogo = {
                            'Time da Casa': team_home,
                            'Time Visitante': team_away,
                            'Status': status,
                        }

                    jogos_campeonato_brasileiro.append(jogo)

        if jogos_campeonato_brasileiro:
            mensagem = '<b>Jogos do Campeonato Brasileiro da Série A:</b>\n\n'
            for jogo in jogos_campeonato_brasileiro:
                if 'Placar Casa' in jogo:
                    mensagem += f"{jogo['Time da Casa']} {jogo['Placar Casa']} - {jogo['Placar Visitante']} {jogo['Time Visitante']} ({jogo['Status']})\n"
                else:
                    mensagem += f"{jogo['Time da Casa']} x {jogo['Time Visitante']} ({jogo['Status']})\n"

            bot.send_message(CHANNEL, mensagem)
        else:
            # Se não houver jogos, envie uma mensagem apropriada
            bot.send_message(CHANNEL, "⚽️ <b>Não temos jogos hoje.</b>")
            print("Nenhum jogo encontrado")
    else:
        print(f"Erro ao acessar a página: {response.status_code}")


def check_news_and_send():
    url = 'https://www.lance.com.br/mais-noticias.html'

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        cards = soup.find_all('div', class_='styles_card__XBZhk')

        if len(cards) > 0:
            for card in cards:
                title = card.find('h3').text.strip()

                link = card.find('a')['href']

                if db.search_title(title):
                    logger.info(f"A notícia '{title}' já foi postada.")
                else:
                    current_datetime = datetime.now() - timedelta(hours=3)
                    date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
                    db.add_news(title, date)

                    image = card.find('img')['src']
                    image = image.replace('/width=3840', '/width=512')

                    button_text = (
                        f'https://www.lance.com.br{link}'  
                    )
                    markup = types.InlineKeyboardMarkup()
                    btn_news = types.InlineKeyboardButton(
                        text='Ver notícia completa', url=button_text
                    )
                    markup.add(btn_news)

                    bot.send_photo(
                        CHANNEL,
                        photo=image,
                        caption=f'<b>{title}</b>\n\n<code>{date}</code>',
                        reply_markup=markup,
                    )
                    sleep(3600)
        else:
            logger.info('Não foram encontradas notícias.')
    else:
        logger.info('Falha ao obter a página')


def scrape_website(url='https://www.lance.com.br/futebol-nacional/mais-noticias.html'):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            articles = soup.find_all(
                'div', class_='styles_card__XBZhk'
            )

            for article in articles:
                title = article.find('h3').text.strip()
                image_url = article.find('img')['src']
                date = article.find(
                    'div', class_='styles_date__lZuoR'
                ).text.strip()

                author_elem = article.find(
                    'span', style='color: var(--green-lance);'
                )
                author = (
                    author_elem.text.strip()
                    if author_elem
                    else 'Autor não encontrado'
                )

                link_elem = article.find('a')
                link = (
                    link_elem['href']
                    if link_elem
                    else 'Link não encontrado'
                )

                send_to_bot(title, image_url, date, author, link)

    except requests.RequestException as e:
        logger.info(f'Request Exception: {e}')


def resize_image(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.resize((512, 512), Image.ANTIALIAS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return buffered.getvalue()
    except Exception as e:
        logger.error(f"Erro ao redimensionar imagem: {e}")
        return None


def send_to_bot(title, image_url, date, author, link):
    try:
        if db.search_title(title):
            logger.info(f"A notícia '{title}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title, date)
        resized_image = resize_image(image_url)

        button_text = f'https://www.lance.com.br{link}' 
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(
            text='Ver notícia completa', url=button_text
        )
        markup.add(btn_news)
        if resized_image:
            bot.send_photo(
                CHANNEL,
                photo=image_url,
                caption=f'<b>{title}</b>\n\n<code>{date}</code> - Feito por: {author}',
                reply_markup=markup,
            )
            sleep(3600)
            pass
        else:
            logger.error("Falha ao redimensionar imagem.")
    except Exception as e:
        logger.info(f'Request Exception: {e}')

def ultimos_jogos():
    try:
        url = 'https://www.lance.com.br/resenha-de-apostas/mais-noticias?page=1'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        all_news = soup.find_all('a', class_='')

        brasileirao_titles = []
        brasileirao_images = []
        brasileirao_dates = []
        brasileirao_links = []

        for news in all_news:
            title = news.find('p', class_='text-more-news-title-desk-lg')
            image = news.find('img', class_='rounded-normal')
            date = news.find('p', class_='text-more-news-date-desk-lg')
            link = 'https://www.lance.com.br' + news['href']

            if title and title.text.startswith('Brasileirão'):
                title_text = title.text
                image_url = image['src'].replace('/width=3840', '/width=512')
                date_text = date.text
                link_text = link

                brasileirao_titles.append(title_text)
                brasileirao_images.append(image_url)
                brasileirao_dates.append(date_text)
                brasileirao_links.append(link_text)

                send_photo_lance(title_text, image_url, date_text, link_text)

    except requests.RequestException as e:
        logger.info(f'Request Exception: {e}')


def send_photo_lance(title_text, image_url, date_text, link_text):
    try:
        if db.search_title(title_text):
            logger.info(f"A notícia '{title_text}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title_text, date)

        button_text = f'https://www.lance.com.br{link_text}'
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(
            text='Ver notícia completa', url=button_text
        )
        markup.add(btn_news)

        bot.send_photo(
            CHANNEL,
            photo=image_url,
            caption=f'<b>{title_text}</b>\n\n<code>{date_text}</code>',
            reply_markup=markup,
        )
        sleep(3600)
    except Exception as e:
        logger.info(f'Request Exception: {e}')


def fora_do_campo():
    try:
        url = 'https://www.lance.com.br/fora-de-campo/mais-noticias.html'

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            news_list = soup.find('ul', class_='styles_list__7maJJ')

            if news_list:
                for news_item in news_list.find_all('li'):
                    title = news_item.find('h3').text.strip()

                    image_url = (
                        'https://www.lance.com.br'
                        + news_item.find('img')['src']
                    )

                    datetime_str = news_item.find(
                        'div', class_='styles_date__lZuoR'
                    ).text.strip()

                    link = news_item.find('a')['href']

                    author = news_item.find(
                        'span', style='color:var(--green-lance)'
                    )
                    author_name = (
                        author.text if author else 'Autor não disponível'
                    )

                    send_text_fora_do_campo(
                        title, image_url, datetime_str, author_name, link
                    )

            else:
                logger.info('Lista de notícias não encontrada.')
        else:
            logger.info('Falha ao obter a página.')
    except requests.RequestException as e:
        logger.info(f'Request Exception: {e}')


def send_text_fora_do_campo(title, image_url, datetime_str, author_name, link):
    try:
        if db.search_title(title):
            logger.info(f"A notícia '{title}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title, date)

        button_text = f'https://www.lance.com.br{link}'
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(
            text='Ver notícia completa', url=button_text
        )
        markup.add(btn_news)

        bot.send_photo(
            CHANNEL,
            photo=image_url,
            caption=f'<b>{title}</b>\n\n<code>{datetime_str}</code> - Feito por {author_name}',
            reply_markup=markup,
        )
        sleep(3600)
    except Exception as e:
        logger.info(f'Request Exception: {e}')


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
                date_time = post.find(
                    'div', class_='styles_date__lZuoR'
                ).text.strip()
                author_tag = post.find(
                    'span', style='color:var(--green-lance)'
                )
                if author_tag:
                    author = author_tag.text.strip()
                else:
                    author = 'Author Not Found'
                post_url = post.find('a')['href']

                send_libertadores_text(
                    title, image_url, date_time, author, post_url
                )
        else:
            logger.info('Failed to retrieve the webpage')
    except requests.RequestException as e:
        logger.info(f'Request Exception: {e}')


def send_libertadores_text(title, image_url, date_time, author, post_url):
    try:
        if db.search_title(title):
            logger.info(f"A notícia '{title}' já foi postada.")
        else:
            current_datetime = datetime.now() - timedelta(hours=3)
            date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
            db.add_news(title, date)

        resized_image = resize_image(image_url)
        button_text = f'https://www.lance.com.br{post_url}'
        markup = types.InlineKeyboardMarkup()
        btn_news = types.InlineKeyboardButton(
            text='Ver notícia completa', url=button_text
        )
        markup.add(btn_news)
        if resized_image:
            bot.send_photo(
                CHANNEL,
                photo=image_url,
                caption=f'<b>{title}</b>\n\n<code>{date_time}</code> - Feito por: {author}',
                reply_markup=markup,
            )
            sleep(3600)
            pass
        else:
            logger.error("Falha ao redimensionar imagem.")
    except Exception as e:
        logger.info(f'Request Exception: {e}')


def check_match_status():
    try:
        url = 'https://www.placardefutebol.com.br/brasileirao-serie-a'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        matches = soup.find_all('h3', class_='match-list_league-name')
        for match in matches:
            if match.text.strip() == 'Campeonato Brasileiro':
                match_info = match.find_next('a')
                match_time = match_info.find(
                    'span', class_='status-name').text.strip()
                match_teams = match_info.find_all('h5', class_='team_link')
                home_team = match_teams[0].text.strip()
                away_team = match_teams[1].text.strip()

                if 'MIN' in match_time:
                    send_message_to_channel(
                        f'A partida entre {home_team} e {away_team} começou!'
                    )
                else:
                    logger.info(
                        f'A partida entre {home_team} e {away_team} não começou ainda. Status: {match_time}'
                    )
    except Exception as e:
        logger.error(f'Erro ao verificar o status da partida: {e}')


def status_gol():
    try:
        url = 'https://www.placardefutebol.com.br/'
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        matches = soup.find_all('div', {'class': 'match-card-events'})

        for match in matches:
            try:
                gols = match.find_all('i', {'class': 'fa fa-futbol-o'})
                if gols:
                    teams = match.find_all('div', {'class': 'team-name'})
                    team_names = [team.text.strip() for team in teams]

                    scores = match.find('div', {'class': 'match-score'})
                    score_text = scores.text.strip().replace('\n', ' x ')

                    goal_team = (
                        gols[0]
                        .find_previous('div', {'class': 'team-name'})
                        .text.strip()
                    )

                    message = f'Gooooooooooooool!!\nGolaço do {goal_team}\nPartida está:\n{team_names[0]} {score_text} {team_names[1]}'

                    send_message_to_channel(message)
            except Exception as e:
                logger.error(f'Erro: {e}')
    except Exception as e:
        logger.error(f'Erro ao obter os dados da página: {e}')


def send_message_to_channel(message):
    try:
        bot.send_message(CHANNEL, text=message)
        logger.info(f'Mensagem enviada para o canal: {message}')
    except Exception as e:
        logger.error(f'Falha ao enviar mensagem para o canal: {e}')

def send_images_to_telegram():
    nome_arquivo_artilheiros, nome_arquivo_assistencias = news.artilheiro.main()  # Chama a função que gera as imagens

    if nome_arquivo_artilheiros and nome_arquivo_assistencias:
        # Enviar a imagem de artilheiros para o canal do Telegram
        with open(nome_arquivo_artilheiros, 'rb') as artilheiros_img:
            bot.send_photo(CHANNEL, artilheiros_img, caption="Imagem de Artilheiros")

        # Enviar a imagem de assistências para o canal do Telegram
        with open(nome_arquivo_assistencias, 'rb') as assistencias_img:
            bot.send_photo(CHANNEL, assistencias_img, caption="Imagem de Assistências")

        # Deletar as imagens após o envio
        os.remove(nome_arquivo_artilheiros)
        os.remove(nome_arquivo_assistencias)
    else:
        logger.error("Não foi possível gerar as imagens.")

# Função para enviar a imagem de artilheiros
def send_artilheiros():
    nome_arquivo_artilheiros, _ = news.artilheiro.main()  # Chama a função que gera a imagem de artilheiros

    if nome_arquivo_artilheiros:
        with open(nome_arquivo_artilheiros, 'rb') as artilheiros_img:
            caption_artilheiros = """
            <b>🎯 Detalhe dos Artilheiros Brasileiros 2024</b>\n
            ⚽ Confira os principais artilheiros do campeonato! \n
            <i>As estatísticas e desempenho estão atualizados.</i>\n\n
            <blockquote>Acesse mais em @fut_br</blockquote>
            """
            bot.send_photo(CHANNEL, artilheiros_img, caption=caption_artilheiros, parse_mode='HTML')

        # Deletar a imagem após o envio
        os.remove(nome_arquivo_artilheiros)
    else:
        logger.error("Não foi possível gerar a imagem dos artilheiros.")

# Função para enviar a imagem de assistências
def send_assistencias():
    _, nome_arquivo_assistencias = news.artilheiro.main()  # Chama a função que gera a imagem de assistências

    if nome_arquivo_assistencias:
        with open(nome_arquivo_assistencias, 'rb') as assistencias_img:
            caption_assistencias = """
            <b>🅰️ Detalhe das Assistências Brasileiras 2024</b>\n
            🎉 Veja quem são os maiores assistentes do campeonato! \n
            <i>Fique por dentro dos melhores desempenhos.</i>\n\n
            <blockquote>Acesse mais em @fut_br</blockquote>
            """
            bot.send_photo(CHANNEL, assistencias_img, caption=caption_assistencias, parse_mode='HTML')

        # Deletar a imagem após o envio
        os.remove(nome_arquivo_assistencias)
    else:
        logger.error("Não foi possível gerar a imagem das assistências.")

def send_tabela():
    _, nome_arquivo_recortado = news.tabela.fut_brasileirao()  # Chama a função que gera a imagem da tabela

    if nome_arquivo_recortado:
        with open(nome_arquivo_recortado, 'rb') as tabela_img:
            caption_tabela = """
            <b>⚽️ Tabela do Campeonato Brasileiro 2024</b>\n
            📊 Confira a classificação atualizada do campeonato!\n
            <i>Fique por dentro dos detalhes das equipes e suas performances.</i>\n\n
            <blockquote>Acesse mais em @fut_br</blockquote>
            """
            bot.send_photo(CHANNEL, tabela_img, caption=caption_tabela, parse_mode='HTML')

        # Deletar a imagem após o envio
        os.remove(nome_arquivo_recortado)
    else:
        logger.error("Não foi possível gerar a imagem da tabela.")


def schedule_tasks():
    schedule.every(1).minutes.do(check_match_status)
    schedule.every(1).minute.do(status_gol)
    schedule.every(15).minutes.do(send_news_g1)
    schedule.every(15).minutes.do(check_news_and_send)
    schedule.every(15).minutes.do(scrape_website)
    schedule.every(15).minutes.do(libertadores)
    schedule.every(15).minutes.do(fora_do_campo)
    schedule.every(15).minutes.do(ultimos_jogos)
    schedule.every(6).hours.do(placar_de_jogo)
    schedule.every().day.at('08:00').do(send_artilheiros)
    schedule.every().day.at('14:00').do(send_assistencias)
    schedule.every(6).hours.do(send_tabela)
    schedule.every().day.at('00:00').do(delete_news)
    schedule.every().day.at('23:58').do(total_news)


def main():
    try:
        logger.info('BOT INICIANDO...')
        schedule_tasks()

        while True:
            schedule.run_pending()
            sleep(1)
    except KeyboardInterrupt:
        logger.info(
            'Encerrando o bot devido ao comando de interrupção (Ctrl+C)'
        )
    except Exception as e:
        logger.exception(f'Erro não tratado: {str(e)}')


if __name__ == '__main__':
    main()
