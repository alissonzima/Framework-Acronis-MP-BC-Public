"""
Esse é o arquivo de métodos gerais de manipulação de dados dos sistema.

 Autor: 
  Álisson Zimermann
 Data: 
  29/03/2023
 
 Explicação: 
  Aqui temos cinco métodos gerais de manipulação de dados.
    - O primeiro é apenas um teste para geração de um anagrama conforme o nome do cliente no BotConversa.
    - O segundo é um método para processar uma imagem. Temos uma imagem base, que é manipulada e retornada ao BotConversa.
    - O terceiro é uma função para gerar um token único para o cliente.
    - O quarto monta e envia um email de validação, para verificar se o email do cliente é válido e ele tem acesso.
    - O quinto retorna para o BotConversa a validação do email.
"""

from urllib.parse import quote
import random
from itertools import permutations
from flask import jsonify
import secrets
import smtplib
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import user_tokens
import requests
import os 


def generate_anagram(name):
    """
    Esse método foi o primeiro teste de comunicação entre esse webservice e o BotConversa. Recebe o nome do cliente,
    de :func:`routes.routes_bc.nome`, cria um anagrama e retorna.

    Parâmetros
    ----------
    name (str) : 
        O nome do cliente para manipulação
        
    Retorno
    -------
    anagram (dict) : 
        Retorna um dicionário com a chave
            - 'oi' (str) : O anagrama gerado com o nome do cliente
    """
    # Gera todas as permutações das letras da palavra
    permutations_list = list(permutations(name))
    # Cria uma lista com as permutações como strings
    anagrams_list = [''.join(perm) for perm in permutations_list]
    # Escolhe um anagrama aleatório da lista
    while True:
        random_anagram = random.choice(anagrams_list)
        if random_anagram != name:
            break
    random_anagram = random_anagram.capitalize()
    anagram = {'oi': random_anagram}
    return jsonify(anagram)

def processa_imagem(data):
    """
    Esse método recebe os dados do cliente de :func:`routes.routes_bc.envia_imagem`, abre a imagem padrão,
    desvira ela, insere os dados do cliente, gira ela novamente, faz o upload da mesma no site imgbb via API
    e, logo após, retorna para o BotConversa o link da imagem pronta, conforme mostrado à seguir:
    
    .. image:: base_image.png
        :alt: Post it
        :align: center
        :scale: 15%

    Parâmetros
    ----------
    data (dict): 
        Um dicionário de dados com as seguintes informações do cliente:
        - 'nome' (str) : O primeiro nome do cliente
        - 'telefone' (str) : O telefone do cliente, chave de busca do BotConversa
        
    Retorno
    -------
    data (dict) :
        Envia ao webhook do BotConversa um dicionário de dados contendo:
            - 'phone' (str) : O telefone do cliente.
            - 'link' (str) : O link da imagem pronta criada.
    """
    from PIL import Image, ImageDraw, ImageFont
    import requests
    import math

    # obter caminho absoluto do diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # concatenar com o caminho relativo da imagem
    image_path = os.path.join(current_dir, 'base_image.png')
    
    # carregar a imagem base
    base_image = Image.open(image_path)

    # obter largura e altura da imagem
    largura, altura = base_image.size

    # define a inclinação desejada em graus
    angulo_inclinacao = -3.10

    # rotaciona a imagem para remover a inclinação original
    base_image = base_image.rotate(angulo_inclinacao, expand=True)

    # configura a fonte e tamanho do texto
    fonte = ImageFont.truetype(os.path.join(current_dir, 'LHANDW.TTF'), size=80)

    # cria o objeto draw para desenhar na imagem
    draw = ImageDraw.Draw(base_image)
    print(data)
    nome = data['nome']
    nome_completo = data['nome_completo']
    telefone = '(' + data['telefone'][3:5] + ') ' + data['telefone'][5:]

    # obtém o tamanho do texto a ser inserido
    texto = f'Falar com {nome}\nTel. {telefone}'

    # divide o texto em linhas
    linhas = texto.split('\n')

    # obtém a largura e altura de cada linha de texto
    largura_linhas = []
    altura_linhas = []
    for linha in linhas:
        largura_texto, altura_texto = draw.textsize(linha, font=fonte)
        largura_linhas.append(largura_texto)
        altura_linhas.append(altura_texto)

    # obtém a largura e altura totais do bloco de texto
    largura_total = max(largura_linhas)
    altura_total = sum(altura_linhas)

    # define a posição inicial para o texto
    pos_x = largura // 2 - largura_total // 2

    # define a posição vertical para a primeira linha de texto
    pos_y = math.ceil(0.40 * altura)

    # desenha o bloco de texto na imagem
    for i, linha in enumerate(linhas):
        largura_texto, altura_texto = draw.textsize(linha, font=fonte)

        # calcula a posição horizontal para centralizar a linha
        pos_x_linha = pos_x + (largura_total - largura_texto) // 2

        # desenha a linha na imagem
        draw.text((pos_x_linha, pos_y), linha, font=fonte, fill=(0, 0, 0))

        # atualiza a posição vertical para a próxima linha de texto
        pos_y += math.ceil(0.10 * altura) + altura_texto

    # rotaciona a imagem de volta para a inclinação desejada
    base_image = base_image.rotate(-angulo_inclinacao, expand=True)

    # salva a imagem com o texto inserido
    base_image.save('imagem_com_texto.png')

    with open('imagem_com_texto.png', 'rb') as f:
        response = requests.post('https://api.imgbb.com/1/upload', 
                                data={'key': 'put_key'},
                                files={'image': f})
        
    if response.status_code == 200:
        data = response.json()['data']
        link = data['url']
        print('Link para a imagem:', link)
    else:
        print('Erro:', response.status_code)
        
   
    #print('pagamento ' + str(pagamento))
    webhook_bc = 'put_webhook_botconversa'    

    data = {
        'phone' : telefone,
        'link' : link,
        'nome' : nome_completo
    }

    response = requests.post(webhook_bc, data=data)
    
    return data

def generate_token(email):
    """
    Função criada apenas para gerar o token único do cliente para validação do email.
    Recebe o email de :func:`services.methods.enviar_email_validacao` e utiliza o módulo 'secrets' para
    gerar o token.

    Parâmetros
    ----------
    email (str) : 
        O email do cliente.
        
    Retorno
    -------
    token (str) : 
        Token a ser enviado por email para validação.
    """    
    token = secrets.token_urlsafe()
    user_tokens[email] = token
    print(user_tokens)
    return token   

def enviar_email_validacao(data) :
    """
    Método criado para enviar ao cliente um email para verificar se o mesmo é válido e o cliente tem acesso.
    Recebe os dados de :func:`routes.routes_bc.webhook_bc`, gera um token em :func:`services.methods.generate_token`
    e monta um modelo de email enviando por link esses dados todos para serem validados pelo cliente. Ao clicar no
    link, o mesmo é redirecionado ao endpoint :func:`routes.routes_bc.valida_email`

    Parâmetros
    ----------
    data (dict): 
        Um dicionário de dados com as seguintes informações do cliente:
        - 'email' (str) : Email do cliente
        - 'telefone' (str) : O telefone do cliente
    """      
    telefone = data['telefone']
    nome = quote(data['nome'])
    to = data['email']
    token = generate_token(to)
    link = f'put_api_link/valida_email?email={to}&token={token}&phone={telefone}&nome={nome}'
    subject = 'Validação de e-mail'
        
    html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>E-mail de validação</title>
            <style type="text/css">body {{background-color: #f2f2f2;font-family: Arial, sans-serif;}}.container {{margin: 20px auto;max-width: 700px;padding: 20px;background-color: #fff;border-radius: 5px;box-shadow: 0px 0px 10px #ccc;text-align: center;}}h1 {{color: #3e3e3e;}}.pe {{color: #666;font-size: 18px;line-height: 1.5;margin-bottom: 20px;}}.button {{background-color: #0066cc;color: #fff !important;display: inline-block;padding: 10px 20px;border-radius: 5px;text-decoration: none;transition: background-color 0.2s;}}.button:hover {{background-color: #0052a3;}}p, li, div {{margin: 0;font-size: 11pt;font-family: Calibri, sans-serif;}}td {{padding: 0cm 5.4pt;}}.img-gen {{width: 100%;height: auto;}}.support-text {{font-size: 14.0pt;font-family: \'Arial\', sans-serif;color: #767171;}}.support-text b {{color: #333d53;}}.support-phone {{color: #767171;}}.support-phone span {{font-family: Arial, sans-serif;}}.support-address {{color: #767171;font-weight: bold;}}.support-social {{font-family: "Arial", sans-serif;color: #767171;text-align: center;}}.support-quote {{font-size: 9.0pt;color: #767171;font-weight: bold;text-align: center;}}</style>
        </head>
        <body>
            <div class="container">
                <h1>VALIDAÇÃO DE E-MAIL</h1>
                <p class="pe">Obrigado por fazer seu pedido de compra conosco.</p>
                <p class="pe">Para validar seu e-mail, clique no botão abaixo:</p>
                <a href="{link}" class="button">Validar e-mail</a>
            <p>&nbsp;</p>
            <table border=0 cellspacing=0 cellpadding=0 width=397 style=\'width:297.95pt;margin-left:-7.35pt\'>
                <tr>
                    <td width=397 valign=top style=\'width:297.95pt;height:26.2pt\'>
                    <table border=0 cellspacing=0 cellpadding=0 width=680 style=\'width:510.0pt\'>
                        <tr style=\'height:26.2pt\'><td width=208 rowspan=3 style=\'width:155.95pt;border:none;border-right:solid #333d53 1.5pt;height:26.2pt\'><img src="put_source" class="img-gen"></td></tr>
                        <tr>
                            <td width=454 valign=top style=\'width:12.0cm;height:116.35pt\'>
                                <p class="support-text"><b>Suporte Técnico</b></p>
                                <p class="support-phone">put_phone</p>
                                <p class="support-phone">put_celphone <span style="color: #833C0B; font-size: 9.0pt">(Whatsapp)</span></p>
                                <p><b><span style=\'color:#833C0B;\'>&nbsp;</span></b></p>
                                <p class="support-address">put_address<br><a href=\'put_href\'>put_href</a></p>
                                <p>&nbsp;</p>
                            </td>
                        </tr>
                        <tr style=\'height:20.95pt\'>
                            <td width=454 valign=top style=\'width:12.0cm;height:20.95pt\'>
                                <p class="support-social">put_social_media</p>
                            </td>
                        </tr>
                        </div>
                    </table>
                    </td>
                </tr>
                
            </table>
            
        </body>
        </html>
    '''
    
    # credenciais do remetente
    email = 'put_naoresponda'
    password = 'put_password'
    #print(html)
    '''
    fazer try catch, deu erro de smtp uma vez
    
    '''
    # configuração do servidor SMTP do Gmail
    smtp_server = 'smtp.terra.com.br'
    smtp_port = 587

    tentativas = 3 # número de tentativas de reenvio

    for i in range(tentativas):
        try:

            # conexão com o servidor SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email, password)

            # criação do objeto de mensagem
            message = MIMEMultipart("alternative")
            
            # criação da parte HTML
            html_part = MIMEText(html, "html")
            
            # anexando a parte HTML à mensagem
            message.attach(html_part)
            
            message['Subject'] = subject
            message['From'] = email
            message['To'] = to

            # envio do e-mail
            server.send_message(message, from_addr=email, to_addrs=[to])
            server.quit()
            
            print('E-mail enviado com sucesso!')
            break
        
        except SMTPException as e:
            print(f'Erro ao enviar e-mail: {e}')
            if i < tentativas - 1:
                print('Tentando reenviar...')
    
    return '204'

def validacao_email(telefone, validacao, nome) :
    """
    Esse método recebe os dados de :func:`routes.routes_bc.valida_email` e, caso tenha sido validado com sucesso,
    envia ao webhook do BotConversa essa confirmação.

    Parâmetros
    ----------
    telefone (str) : 
        Telefone do cliente, chave primária de pesquisa do BotConversa 
    validacao (str) : 
        O texto de confirmação retornado pelo método que o chamou. Não tem outra função a não ser prevenir várias confirmações e várias chamadas para o webhook repetidas
    """      
    webhook_bc_email = 'put_webhook_botconversa'
    
    data = {
        'phone' : telefone,
        'validacao' : validacao,
        'nome' : nome
    }
    response = requests.post(webhook_bc_email, data=data)            
    print(response.text)
