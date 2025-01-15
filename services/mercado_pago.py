"""
Esse é o arquivo de métodos para manipular transações a respeito do Mercado Pago

 Autor: 
  Álisson Zimermann
 Data: 
  28/03/2023
 
 Explicação: 
  Aqui temos dois métodos, o primeiro que irá gerar o link de pagamento conforme a compra do usuário.
  O segundo método recebe a resposta a respeito do pagamento do cliente e compara com os dados em memória
  enviando a resposta para o BotConversa seguir o fluxo.

 Disclaimer - Esse método foi alterado para trabalhar com ASAAS ao invés de mercado pago, mantendo-se o nome do arquivo por conveniência.
"""

#import mercadopago
from config import memory
import requests
from prices.licencas import licencas
from prices.planos import planos
from flask import jsonify
from datetime import datetime, timedelta
import json

webhook_bc = 'put_webhook_botconversa'
token_asaas = 'put_token_asaas'

def encontrar_plano(dados_usuario):
    if dados_usuario['plano']:
            for item in licencas:
                if item['nome'] == dados_usuario['plano']:
                    dados_usuario['qtd_licencas'] = int(item['qtd_pc']) + int(item['qtd_mobile']) + int(item['qtd_server'])
                    
            for item in planos:
                if item['nome'] == dados_usuario['item_compra'] + ' ' + dados_usuario['plano'][-1]:
                    if item['cobranca'] == dados_usuario['cobranca'] :
                        if item['volume'] == dados_usuario['qtd_espaco']  :
                            dados_usuario['valor_plano'] = item['valor']
    elif 'Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra'] :
        for item in planos:
            if dados_usuario['item_compra'] == item['nome'] :
                valor = item['valor'].replace(',', '.')
                dados_usuario['valor_plano'] = float(dados_usuario['qtd_licencas']) * float(valor)
    else :
        for item in planos:
            if item['nome'] == dados_usuario['item_compra'] :
                if item['cobranca'] == dados_usuario['cobranca'] :
                    if item['volume'] == dados_usuario['qtd_espaco']  :
                        dados_usuario['valor_plano'] = item['valor']


def gerar_link(dados_usuario) :
    """
    Esse método é responsável por gerar o link de pagamento do Asaas. Recebe os dados de :func:`routes.routes_mp.criar_venda`.

    Parâmetros
    ----------
    dados_usuario : dict
        Um dicionário contendo os dados do usuário. Deve conter os seguintes atributos:
        
        - 'cobranca' (str) : O método de cobrança, se por 'Workload' ou por 'Volume'
        - 'telefone' (str) : O telefone do cliente
        - 'qtd_espaco' (int) : A quantidade de espaço contratada, caso 'cobranca' seja 'Volume'
        - 'item_compra' (str) : A descrição do pacote adquirido pelo cliente
        - 'qtd_licencas' (int) : Quantidade de licenças adquiridas pelo cliente, caso 'cobranca' seja 'Workload'  
         
    Retorno
    -------
    preference['init_point'] : str
        O link do Asaas contendo o item e o valor a ser pago pelo cliente.
    """
    
    encontrar_plano(dados_usuario)
    valor_plano = dados_usuario.get('valor_plano', None)
    
    if valor_plano:
        print(f'O valor do plano é: {valor_plano}')
    else:
        print('Plano não encontrado')
        
    if 'Notary' in dados_usuario['item_compra'] :
        title = 'Plano ' + dados_usuario['item_compra'] + ' com ' + dados_usuario['qtd_espaco'] + 'mb'
    elif 'Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra']:
        title = str(dados_usuario['qtd_licencas']) + ' licenças de ' + dados_usuario['item_compra']
    elif dados_usuario['qtd_licencas']:
        title = str(dados_usuario['qtd_licencas']) + ' licenças de ' + dados_usuario['title'] + ' ' + str(dados_usuario['qtd_espaco']) + 'gb'
    else:
        title = dados_usuario['title'] + ' ' + dados_usuario['qtd_espaco'] + 'gb'
        
    url = 'https://sandbox.asaas.com/'

    # Pegar a data atual
    today = datetime.now()

    # Avançar 3 dias
    three_days_later = today + timedelta(days=3)

    # Exibir no formato desejado
    formatted_date = three_days_later.strftime('%Y-%m-%d')
    
    headers = {
        'Content-Type' : 'application/json',
        'access_token' : token_asaas
    }
        
    print(title)
    compra = {
        "name": title,
        "description": title,
        "endDate": formatted_date,
        "value": valor_plano,
        "billingType": "CREDIT_CARD",
        "chargeType": "RECURRENT",
        "subscriptionCycle": "MONTHLY",
        "notificationEnabled": True
    }    
    
    response = requests.post(url + 'api/v3/paymentLinks', headers=headers, json=compra)
    print(response.text)
    pedido = json.loads(response.text)
    # Aqui o telefone do cliente é inserido em memória para confrontar com o retorno do Asaas
    memory.append({'telefone' : dados_usuario['telefone'],
                   'id_pedido' : pedido['id'],
                   'nome' : dados_usuario['nome']})
    
    return pedido['url']
    
    '''
    # Cria um item na preferência
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(valor_plano)
            }
        ],
        "payer": {
            "phone": {
            'area_code' : dados_usuario['telefone'][3:5],
            'number' : dados_usuario['telefone'][5:]
            }
        }
    }
    print(preference_data)
    #print('memory no gera link')
    #print(memory)
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    print(preference)
    return preference['init_point']
    
    # Cria um item em preapproval
    data = {
        
    "reason": title,
    "quantity": 1,
    "unit_price": float(valor_plano),
    "payer_email": dados_usuario['email'],
    "back_url": "put_back_url",
    "auto_recurring": {
        "currency_id": "BRL",
        "frequency": 1,
        "frequency_type": "months",
        "transaction_amount": 30.0, 
        "currency_id": "BRL",
        "auto_renew": True
        }
    }
    
    preapproval_response = sdk.preapproval().create(data)
    preapproval = preapproval_response["response"]
    print(preapproval)
    return preapproval['init_point']
    
    # Defina os dados do pagamento
    data = {
        "email": "put_email",
        "token": "put_token",
        "currency": "BRL",
        "itemId1": "1",
        "itemDescription1": title,
        "itemAmount1": float(valor_plano),
        "itemQuantity1": "1",
        "senderName": "Nome do Cliente",
        "senderEmail": "email@cliente.com",
        "senderAreaCode": "11",
        "senderPhone": "999999999",
        "shippingAddressStreet": "Rua do Cliente",
        "shippingAddressNumber": "123",
        "shippingAddressComplement": "Apto 456",
        "shippingAddressDistrict": "Bairro do Cliente",
        "shippingAddressPostalCode": "12345678",
        "shippingAddressCity": "São Paulo",
        "shippingAddressState": "SP",
        "shippingAddressCountry": "BRA",
        "notificationURL": "put_notification_url"
    }

    # Faça a requisição para criar a recorrência avulsa
    response = requests.post("https://ws.pagseguro.uol.com.br/v2/transactions", data=data)

    # Verifique a resposta da API
    if response.status_code == 200:
        print("Recorrência criada com sucesso!")
    else:
        print("Erro ao criar recorrência:", response.text)

'''

# função webhook
def confirma_pagamento(pagamento) :
    """
    Esse método é responsável por aguardar uma resposta do Asaas com o ID do pagamento do cliente.
    Após verificar o status do pagamento, comparando com o ID e telefone do cliente armazenados, caso seja
    APRO, ele retorna ao BotConversa para seguir o fluxo de venda. Recebe os dados de Recebe os dados de :func:`routes.routes_mp.webhook_mp`.

    Parâmetros
    ----------
    pagamento : dict
        Um dicionário contendo os dados de pagamento do usuário. Deve conter os seguintes atributos obrigatórios:
        
        - 'data.id' (int) : O ID do pagamento do cliente     
    """
    
    status = ''
    
    webhook_bc = 'put_webhook_botconversa'
    
    headers = {
    'Authorization': 'put_bearer_auth',
    }
    
    print('pagamento ' + str(pagamento))
    
    id_pagamento = pagamento['payment']['paymentLink']
    print ('id pagamento: ' + str(id_pagamento))
    
    if pagamento['event'] == 'PAYMENT_CONFIRMED' :
        status = 'approved'
    
    #print('data ' + str(data))
    #print('data')
    #print(data)
    #print('payer')
    #print(data['payer'])
    #print('phone')
    #print(data['payer']['phone'])
    #print('number')
    #print(data['payer']['phone']['number'])
    ##telefone = "+55" + data['additional_info']['payer']['phone']['area_code'] + data['additional_info']['payer']['phone']['number']
    #print(status)
    ##memory.append({'telefone' : telefone})
    ##print('telefone e memory no webhook')
    ##print(telefone)
    #print(memory.get(telefone))
    ##print(memory)
    #print(type(memory[0]['telefone']))
    #print(type(telefone))
    #print('telefone' in memory.keys())
    resposta = ''
    telefone = None
    id_pedido = next((item for item in memory if item['id_pedido'] == id_pagamento), None)
    if id_pedido is not None:
        resposta = 'existe'
        telefone = id_pedido['telefone']
        nome = id_pedido['nome']
    
    print('status ', status, ' resposta ', resposta) 
    if status == 'approved' and resposta == 'existe' : 
        data = {'phone' : telefone,
                'nome' : nome}
        for item in memory:
            if item.get('telefone') == telefone:
                memory.remove(item)
        response = requests.post(webhook_bc, data=data)
        print(response.text)
        return response
