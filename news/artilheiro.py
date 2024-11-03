from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import time
import datetime
import os  

def main():
    # Configurações do Chrome
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument("--headless")

    # Iniciar o WebDriver
    driver = webdriver.Chrome(options=chromeOptions)
    driver.get('https://www.espn.com.br/futebol/estatisticas/_/liga/bra.1')

    # Gerar o nome do arquivo com a data de hoje
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    nome_arquivo_final = f"tabela_classificacao_completa_{data_atual}.png"
    nome_arquivo_artilheiros = f"artilheiros_{data_atual}.png"
    nome_arquivo_assistencias = f"assistencias_{data_atual}.png"

    try:
        # Esperar até que o elemento da tabela esteja presente na página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="fittPageContainer"]/div[2]/div[2]/div/div/section/div/section/div/div[1]/section/div'))
        )

        # Ocultar o cabeçalho
        driver.execute_script("document.querySelector('header').style.display='none';")

        # Capturar várias imagens enquanto faz scroll para baixo
        partes_imagens = []
        altura_total = driver.execute_script("return document.body.scrollHeight")
        altura_visivel = driver.execute_script("return window.innerHeight")
        scroll_pos = 0

        while scroll_pos < altura_total:
            # Captura de tela da parte visível
            nome_arquivo_parcial = f"parte_{scroll_pos}.png"
            driver.save_screenshot(nome_arquivo_parcial)
            partes_imagens.append(nome_arquivo_parcial)

            # Scroll para baixo
            scroll_pos += altura_visivel
            driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            time.sleep(1)  # Aguardar para garantir que o conteúdo seja carregado

        # Abrir e unir as imagens
        imagens = [Image.open(parte) for parte in partes_imagens]
        largura_total, altura_unica = imagens[0].size
        altura_final = sum(img.size[1] for img in imagens)  # Somar as alturas
        imagem_final = Image.new('RGB', (largura_total, altura_final))

        # Colocar cada imagem na posição correta
        y_offset = 0
        for img in imagens:
            imagem_final.paste(img, (0, y_offset))
            y_offset += img.size[1]  # Atualiza o deslocamento vertical

        # Salvar a imagem completa
        imagem_final.save(nome_arquivo_final)
        print(f"Tabela completa salva como: {nome_arquivo_final}")

        # Cortar e salvar as imagens específicas
        # Recorte para artilheiros
        imagem_artilheiros = imagem_final.crop((28, 326, 28 + 484, 326 + 429))
        imagem_artilheiros.save(nome_arquivo_artilheiros)
        print(f"Imagem de artilheiros salva como: {nome_arquivo_artilheiros}")

        # Recorte para assistências
        imagem_assistencias = imagem_final.crop((509, 327, 509 + 488, 327 + 427))
        imagem_assistencias.save(nome_arquivo_assistencias)
        print(f"Imagem de assistências salva como: {nome_arquivo_assistencias}")

        # Deletar partes de imagens temporárias
        for parte in partes_imagens:
            os.remove(parte)
            print(f"Arquivo {parte} deletado.")

        # Deletar a imagem final
        os.remove(nome_arquivo_final)
        print(f"Arquivo {nome_arquivo_final} deletado.")

        return nome_arquivo_artilheiros, nome_arquivo_assistencias  # Retornar os nomes dos arquivos

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None, None  # Retornar None em caso de erro

    finally:
        # Fechar o WebDriver
        driver.quit()
