import requests
from bs4 import BeautifulSoup

import configparser
from telebot.apihelper import ApiTelegramException
import psutil

import telebot
from telebot import types
import telegraph

from datetime import datetime, timedelta
from time import sleep

import io
import schedule
import db
from loguru import logger


config = configparser.ConfigParser()
config.read('bot.conf')
logger.add(config['LOG']['LOG_PATH'])

TOKEN = config['NEWS']['TOKEN']
GROUP_LOG = int(config['NEWS']['NEWS_LOG'])
CHANNEL = int(config['NEWS']['NEWS_CHANNEL'])
CHANNEL_USERNAME = config['NEWS']['CHANNEL_USERNAME']
BOT_NAME = config['NEWS']['BOT_NAME']
BOT_USERNAME = config['NEWS']['BOT_USERNAME']
OWNER = int(config['NEWS']['OWNER_ID'])
OWNER_USERNAME = config['NEWS']['OWNER_USERNAME']
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
        for section in post_sections[
            :limit
        ]:  # Limitando o número de notícias a serem analisadas
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
                    if (
                        media_element and 'src' in media_element.attrs
                    ):  # Verifica se 'src' está presente nos atributos
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
        
        # Formatação do conteúdo 'full_text'
        paragraphs = [f'<p>{paragraph}</p>' for paragraph in full_text.split('\n\n')]
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


def total_news():
    try:
        all_news = db.get_all_news()
        total_count = len(list(all_news))  # Calculate total count
        bot.send_message(
            GROUP_LOG,
            f'TOTAL de Notícia enviada hoje: <code>{total_count}</code> Notícias',
        )  # Send the total count
    except Exception as e:
        logger.exception(f'Error sending total news count: {str(e)}')

schedule.every().day.at('23:58').do(total_news)

def delete_news():
    try:
        logger.info('Deletando todas as noticias do bnaco de dados...')
        db.remove_all_news()
    except Exception as e:
        logger.exception(
            f'Erro ao deletar as notícias do banco de dados: {str(e)}'
        )


schedule.every().day.at('00:00').do(delete_news)

def send_table_message():
    try:
        # Código para obter a tabela do Brasileirão Serie A
        response = requests.get('https://www.cnnbrasil.com.br/esportes/futebol/tabela-brasileirao-serie-a/')
        content = response.content
        site = BeautifulSoup(content, 'html.parser')

        tabela = site.find('tbody', class_='table__body')

        # Encontrando todas as linhas da tabela
        linhas = tabela.find_all('tr', class_='body__row')

        # Criando a mensagem formatada com a tabela
        message = "<b>Tabela do Brasileirão ⚽️🇧🇷</b>\n\n"
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
                f"🏆 {classificacao} - <b>{nome_time}</b>\n"
                f"Pontos: {pontos} pts\n"
                f"Jogos: {jogos}\n"
                f"V: {vitorias} E: {empates} D: {derrotas}\n"
                f"Saldo de Gols: {saldo_gols}\n"
                f"{'━━━━━━━━━━━━━━━━━━'}\n\n"
            )
            message += table_row

        # Enviar mensagem para o Telegram
        bot.send_message(CHANNEL, message, parse_mode='HTML')
        logger.info('Mensagem da tabela enviada com sucesso para o Telegram.')

    except Exception as e:
        logger.error(f'Erro ao enviar a mensagem da tabela para o Telegram: {str(e)}')

schedule.every(6).hours.do(send_table_message)


def enviar_mensagem():
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

        # Construindo a mensagem a ser enviada
        mensagem = "<b>Jogos do Campeonato Brasileiro da Série A:</b>\n\n"
        for jogo in jogos_campeonato_brasileiro:
            if 'Placar Casa' in jogo:
                mensagem += f"{jogo['Time da Casa']} {jogo['Placar Casa']} - {jogo['Placar Visitante']} {jogo['Time Visitante']} ({jogo['Status']})\n"
            else:
                mensagem += f"{jogo['Time da Casa']} x {jogo['Time Visitante']} ({jogo['Status']})\n"

        # Enviando a mensagem para o canal
        bot.send_message(CHANNEL, mensagem)

# Schedule para enviar a mensagem a cada 6 horas
schedule.every(6).hours.do(enviar_mensagem)

def check_news_and_send():
    # URL da página
    url = 'https://www.lance.com.br/mais-noticias.html'

    # Fazendo a requisição HTTP
    response = requests.get(url)

    if response.status_code == 200:
        # Parseando o HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrando todos os cards de notícias
        cards = soup.find_all('div', class_='styles_card__XBZhk')
        
        # Verificando se existem notícias
        if len(cards) > 0:
            # Enviando cada notícia para o grupo
            for card in cards:
                # Título da notícia
                title = card.find('h3').text.strip()
                
                # URL da notícia
                link = card.find('a')['href']
                
                # Verificando se o título da notícia já está no banco de dados
                if db.search_title(title):
                    print(f"A notícia '{title}' já foi postada.")
                else:
                    current_datetime = datetime.now() - timedelta(hours=3)
                    date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
                    db.add_news(title, date)
                    
                    # URL da imagem
                    image = card.find('img')['src']
                    
                    # Criando o botão com o link desejado
                    button_text = f"https://www.lance.com.br/+link"  # Texto do botão
                    markup = types.InlineKeyboardMarkup()
                    btn_news = types.InlineKeyboardButton(text='Ver notícia completa', url=link)
                    markup.add(btn_news)
                    
                    # Enviar a foto e os detalhes da notícia para o grupo com o botão
                    bot.send_photo(CHANNEL, photo=image, caption=f"<b>{title}</b>\n\n<code>{date}</code>", reply_markup=markup)
                    sleep(100)
        else:
            print("Não foram encontradas notícias.")
    else:
        print("Falha ao obter a página")

# Configurando o schedule para verificar a cada 15 minutos
schedule.every(15).minutes.do(check_news_and_send)

if __name__ == '__main__':
    while True:  # Loop infinito
        try:
            logger.info('Iniciando o bot...')
            created_links = create_telegraph_posts()
            
            for telegraph_link, title, original_link in created_links:
                news_name = db.search_title(title)
                
                if news_name:
                    logger.info('A notícia já foi postada.')
                else:
                    logger.info(
                        'Adicionando notícia ao banco de dados e enviando mensagem...'
                    )
                    current_datetime = datetime.now() - timedelta(hours=3)
                    date = current_datetime.strftime('%d/%m/%Y - %H:%M:%S')
                    db.add_news(title, date)  
                    logger.info('Enviando notícia...')
                    bot.send_message(
                        CHANNEL,
                        f'<a href="{telegraph_link}">󠀠</a><b>{title}</b>\n\n'
                        f'🗞 <a href="{original_link}">G1 SPORTS</a>',
                    )
                    sleep(300)
                    

            logger.info('Todas as notícias foram enviadas para o Telegram.')
            sleep(3600)
            logger.info('Reiniciando a pesquisa após 1h')
            schedule.run_pending()
            sleep(60)
            logger.info('Observando se há schedule')
            
        except Exception as e:
            logger.exception(f'Erro não tratado: {str(e)}')