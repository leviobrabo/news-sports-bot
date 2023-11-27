import schedule
import time
from tabela import send_table_message
from g1sports import create_telegraph_posts, delete_news, total_news

# Agendar envio da tabela às 18h
schedule.every().day.at("17:45").do(send_table_message)

# Agendar envio das notícias para as 18h
schedule.every().day.at('18:00').do(create_telegraph_posts)

# Agendar a contagem total das notícias
schedule.every().day.at('23:58').do(total_news)

# Agendar a limpeza do banco de dados
schedule.every().day.at('00:00').do(delete_news)

if __name__ == '__main__':
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            print(f"Erro não tratado: {str(e)}")
            time.sleep(60)
