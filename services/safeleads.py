import requests
import json
from urllib.parse import quote
from time import sleep
from werkzeug.utils import secure_filename
from flask import jsonify
from datetime import datetime, timedelta

api_url = "put_api_url"

accessToken = 'put_access_token'

headers = {'Content-Type': 'application/json',
            'Authorization' : 'Bearer {}'.format(accessToken)}

def cria_lead(dados_usuario) :
    
    url = api_url + '/api/Lead'

    data = {
        'nome' : dados_usuario['nome'],
        'email' : dados_usuario['email'],
        'celular' : dados_usuario['telefone'],
        'origem' : 'Redes Sociais'
    }

    response = requests.post(url, headers=headers, json=data)

    dados_usuario['id'] = json.loads(response.text)['Content']['id']
    
    return dados_usuario

def define_responsavel(dados_usuario) :

    url = api_url + f'/api/Lead/AlterarResponsavel/{dados_usuario["id"]}'

    params = {
        'usuarioId': put_id,
        'isPreVendedor' : True
    }

    response = requests.put(url, headers=headers, params=params)
    
    params = {
        'usuarioId': put_id,
        'isPreVendedor' : False
    }

    response = requests.put(url, headers=headers, params=params)
    
    return dados_usuario

def adiciona_projeto(dados_usuario) :

    url = api_url + f'/api/Projeto'

    data = {
        "nome": dados_usuario['nome'],
        "leadId": dados_usuario['id'],
        "tipoProjetoId": dados_usuario['sf_edificacao'],
        "consumo": dados_usuario['consumo'],
        "statusId": put_status_id
    }

    response = requests.post(url, json=data, headers=headers)

    dados_usuario['projeto_id'] = json.loads(response.text)['Content']['id']
    
    return dados_usuario

def tipo_telhado(dados_usuario) :
    
    url = api_url + f'/api/Projeto/{dados_usuario["projeto_id"]}'

    data = {
        'propriedade' : 'TipoTelhado',
        'valor' :  dados_usuario['tipo_telhado']
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    data = {
        'propriedade' : 'FaceTelhado',
        'valor' :  'Leste'
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    data = {
        'propriedade' : 'FaseEnergetica',
        'valor' :  dados_usuario['sf_fase'] #ver a variavel que noé vai trazer
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))    
    
    
    return dados_usuario

def concessionaria(dados_usuario) :
    
    url = api_url + f'/api/Projeto/{dados_usuario["projeto_id"]}'

    data = {
        'propriedade' : 'Concessionaria',
        'valor' :  dados_usuario['concessionaria']
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    return dados_usuario

def endereco(dados_usuario) :
    
    bairro = dados_usuario['bairro']
    cep = dados_usuario['cep']
    cidade = dados_usuario['cidade']
    logradouro = dados_usuario['logradouro']
    numero = dados_usuario['numero']
    uf = dados_usuario['uf']

    address = f'{logradouro}, {numero}, {cidade} {uf}'

    geo_url = 'https://geocode.maps.co/search?q={address}'
    print(geo_url.format(address=quote(address)))

    response = requests.get(geo_url.format(address=quote(address)))
    #print(response.status_code)
    #print(response.text)
    
    data = response.json()
    
    if data :
        latitude = data[0]['lat']
        dados_usuario['latitude'] = latitude
         
        longitude = data[0]['lon']
        dados_usuario['longitude'] = longitude
    else :
        geo_url = 'https://geocode.maps.co/search?q={cidade}'
        #print(geo_url.format(address=quote(address)))

        response = requests.get(geo_url.format(cidade=quote(cidade)))
        
        data = response.json()
    
        if data :
        
            latitude = response.json()[0]['lat']
            dados_usuario['latitude'] = latitude
            
            longitude = response.json()[0]['lon']
            dados_usuario['longitude'] = longitude 
        
        else :
            
            latitude = '-29.8425284'
            dados_usuario['latitude'] = latitude
            
            longitude = '-53.7680577'
            dados_usuario['longitude'] = longitude 
            
            dados_usuario['coordenadas'] = None
    
    url = api_url + f'/api/Projeto/EditarEndereco/{dados_usuario["projeto_id"]}'

    json = {
        'bairro' : bairro,
        'cep' : cep,
        'cidade' : cidade,
        'latitude' : latitude,
        'longitude' : longitude,
        'logradouro' : logradouro,
        'numero' : numero,
        'uf' : uf
    }
    #print(json)
    response = requests.put(url, headers=headers, json=json)
    #print(response.text)
    
    return dados_usuario

def ajusta_zoom(dados_usuario) :

    url = api_url + f'/api/Projeto/{dados_usuario["projeto_id"]}'

    json = {
        'propriedade' : 'Zoom',
        'valor' :  14 if 'coordenadas' not in dados_usuario else 2
    }

    response = requests.put(url, headers=headers, json=json)
    
    return dados_usuario

def gerar_proposta(dados_usuario) :

    url = api_url + f'/api/PreProposta/SugestoesAldo/{dados_usuario["projeto_id"]}'

    params = {  'marcaPainel': 'JINKO 470W',
                'Distribuidor' : 'Proprio',
                'Consumo' : dados_usuario['consumo']
            }

    response = requests.get(url, headers=headers, params=params)
    
    dados_usuario['kit_id'] = response.json()['Content']['list'][0]['codigo']

    url = api_url + '/api/PreProposta'

    data = {
        "consumo": dados_usuario['consumo'],
        "modeloId": put_modelo_id,
        "projetoId": dados_usuario['projeto_id'],
        "codigoKit": dados_usuario['kit_id'],
        'todosFinanciamentos' : True,
        'configFinanciamentosIds' : [5,8,9]
    }

    response = requests.post(url, json=data, headers=headers)

    dados_usuario['proposta_id'] = response.json()['Content']['id']
    
    return dados_usuario
    
def gerar_pdf(dados_usuario) :

    url = api_url + f'/api/PreProposta/GerarPDF/{dados_usuario["proposta_id"]}'

    response = requests.get(url, headers=headers)

    link = 'put_link_pdf' + str(dados_usuario["proposta_id"]) + '.pdf'
    
    return link
    

def inicio(dados_usuario) :

    dados_usuario = cria_lead(dados_usuario)
    dados_usuario = define_responsavel(dados_usuario)
    dados_usuario = adiciona_projeto(dados_usuario)
    dados_usuario = tipo_telhado(dados_usuario)
    dados_usuario = concessionaria(dados_usuario)
    dados_usuario = endereco(dados_usuario)
    dados_usuario = ajusta_zoom(dados_usuario)
    dados_usuario = gerar_proposta(dados_usuario)
    link = gerar_pdf(dados_usuario)
    print(dados_usuario)
    if dados_usuario.get('imagem') == '1' :
        
        url = 'put_webhook_botconversa'
        
        requests.post(url, data={'nome' : dados_usuario['nome'], 'telefone': dados_usuario['telefone'], 'link_safeleads': link, 'projeto' : dados_usuario['projeto_id']})
        
    else :
    
        url = 'put_webhook_botconversa'
        
        sleep(50)
        
        requests.post(url, data={'nome' : dados_usuario['nome'], 'telefone': dados_usuario['telefone'], 'link_safeleads': link})
    
    
def upload_arquivos(data, tela, id_projeto) :
    
    url = api_url + '/api/Arquivo'
    
    headersArquivo = {'Authorization' : 'Bearer {}'.format(accessToken)}
    
    headersTarefas = {'Content-Type': 'text/plain',
            'Authorization' : 'Bearer {}'.format(accessToken)}
    
    webhook = 'put_webhook_botconversa'
    
    params = {
        'CategoriaId' : put_id
    }
    
    if tela == 1 :
    
        imagem1 = data['imagem1']
        imagem2 = data['imagem2']
        
        imagem1.filename = secure_filename(imagem1.filename)
        imagem2.filename = secure_filename(imagem2.filename)    
            
        response = requests.post(url, files={'file': (imagem1.filename, imagem1, imagem1.mimetype)}, headers=headersArquivo, params=params)
        nome_imagem1 = response.json()["Content"][0]["id"]
        response = requests.post(url, files={'file': (imagem2.filename, imagem2, imagem2.mimetype)}, headers=headersArquivo, params=params)
        nome_imagem2 = response.json()["Content"][0]["id"]
        
        url = api_url + f'/api/Projeto/{id_projeto}/AdicionarArquivo/{nome_imagem1}'
        response = requests.put(url, headers=headers)
        url = api_url + f'/api/Projeto/{id_projeto}/AdicionarArquivo/{nome_imagem2}'
        response = requests.put(url, headers=headers)    
        
        print(response.text)
        
        nome = response.json()['Content']['lead']['nome']
        telefone = response.json()['Content']['lead']['celular']
        
        requests.post(webhook, data={'nome' : nome, 'telefone': telefone})
        
        return 'Imagens salvas, obrigado'
    
    elif tela == 2 :
    
        pdf = data['pdf']
        
        pdf.filename = secure_filename(pdf.filename) 
            
        response = requests.post(url, files={'file': (pdf.filename, pdf, pdf.mimetype)}, headers=headersArquivo, params=params)
        nome_pdf = response.json()["Content"][0]["id"]
        
        url = api_url + f'/api/Projeto/{id_projeto}/AdicionarArquivo/{nome_pdf}'
        response = requests.put(url, headers=headers)
    
        print(response.text)
        
        nome = response.json()['Content']['lead']['nome']
        telefone = response.json()['Content']['lead']['celular']
        
        requests.post(webhook, data={'nome' : nome, 'telefone': telefone})
        
        return 'PDF salvo, obrigado'
    
    elif tela == 3 :
        print(id_projeto)
        dados = id_projeto
        print(dados)
        id_projeto = dados['id_projeto']
        id_tarefa = dados['id_tarefa']
        imagens = []
        nomes_imagens = []
        num_files = len(data)
        
        for i in range(1, num_files + 1):

            key = f'imagem{i}'
            imagem = data[key]
            imagens.append(imagem)
            #print(imagens)
            
        for imagem in imagens :
            
            imagem.filename = secure_filename(imagem.filename)
            
            #print(imagem.filename, imagem, imagem.mimetype)
            
            response = requests.post(url, files={'file': (imagem.filename, imagem, imagem.mimetype)}, headers=headersArquivo)
            #print(response.json())
            nome_imagem = response.json()["Content"][0]["id"]
            nomes_imagens.append(nome_imagem)
            
        for imagem in nomes_imagens :
            
            url = api_url + f'/api/Tarefa/{id_tarefa}/Arquivo/{imagem}'
            print(url)
            response = requests.post(url, headers=headersTarefas)
            
            #print(response.json())
        
        return 'Tarefa gerada com a imagem, obrigado'

def insere_tarefa(data) :
    
    print(data)
    motivo = data['motivo']
    nome = data['nome']
    telefone = data['telefone']
    id_projeto = data['id_projeto']
    url_tarefa = api_url + '/api/tarefa'
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    tomorrow = now + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d %H:%M:%S')
    
    if id_projeto == 11375 :
          descricao = f"{motivo} de {nome} {telefone}"
          titulo = f"Manutenção de {nome}"
          usuariosIds = [5] # Ariel
    elif id_projeto == 11376 :
          descricao = f"{motivo} de {nome} {telefone}"
          titulo = f"Expansão de {nome}"
          usuariosIds = [24] # Noé
    elif id_projeto == 11377 :
          descricao = f"{motivo} de {nome} {telefone}"
          titulo = f"Limpeza de painéis de {nome}"
          usuariosIds = [24] # Noé
          
    json = { "descricao" : descricao,
        "titulo" : titulo,
        "statusId" : 1,
        "dataInicial" : now_str,
        "dataEntrega" : tomorrow_str,
        "projetoId" : id_projeto,
        "tipoId" : 10,
        'usuariosIds' : usuariosIds 
    }
            
    response = requests.post(url_tarefa, json=json, headers=headers)
    
    print(response.text)

    id_tarefa = response.json()['Content']['id']
    
    data = {'id_tarefa': id_tarefa}
    return jsonify(data)
