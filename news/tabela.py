from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import os  # Importar a biblioteca os para manipulação de arquivos

def fut():
    # Configurações do Chrome
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument("--headless")

    # Iniciar o WebDriver
    driver = webdriver.Chrome(options=chromeOptions)
    driver.get('https://www.cnnbrasil.com.br/esportes/futebol/tabela-do-brasileirao/')

    # Gerar o nome do arquivo com a data de hoje
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    nome_arquivo_final = f"tabela_classificacao_completa_{data_atual}.png"

    try:
        # Esperar até que o elemento da tabela esteja presente na página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/section/div/div/div[1]/div[2]'))
        )

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
        imagem_final = Image.new('RGB', (largura_total, altura_total))

        # Colocar cada imagem na posição correta
        y_offset = 0
        for img in imagens:
            imagem_final.paste(img, (0, y_offset))
            y_offset += altura_unica

        # Definir as dimensões e a posição do recorte
        posicao_x = 19
        posicao_y = 412
        largura_recorte = 643
        altura_recorte = 997

        # Realizar o recorte
        imagem_recortada = imagem_final.crop((posicao_x, posicao_y, posicao_x + largura_recorte, posicao_y + altura_recorte))

        # Adicionar texto à imagem recortada
        draw = ImageDraw.Draw(imagem_recortada)
        texto = "@fut_br"
        
        # Carregar uma fonte
        fonte = ImageFont.load_default(20)  # Usando fonte padrão; você pode usar uma fonte TTF se preferir

        # Definindo a posição do texto
        posicao_texto = (483, 10)
        
        # Desenhar o texto na imagem
        draw.text(posicao_texto, texto, fill="black", font=fonte)

        # Salvar a imagem recortada com o texto
        nome_arquivo_recortado = f"tabela_{data_atual}.png"
        imagem_recortada.save(nome_arquivo_recortado)
        print(f"Tabela recortada e texto adicionado salva como: {nome_arquivo_recortado}")

        
        # Deletar as partes das imagens
        for parte in partes_imagens:
            try:
                os.remove(parte)  # Remove o arquivo
                print(f"Arquivo {parte} deletado.")
            except Exception as e:
                print(f"Erro ao deletar o arquivo {parte}: {e}")
        
        return nome_arquivo_recortado
    
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    finally:
        # Fechar o WebDriver
        driver.quit()
