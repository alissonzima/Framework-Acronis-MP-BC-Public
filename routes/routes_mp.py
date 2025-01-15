"""
Esse é uma blueprint que condensa os endpoints de comunicação na parte do Mercado Pago.

 Autor: 
  Álisson Zimermann
 Data: 
  28/03/2023
 
 Explicação: 
  Aqui temos dois endpoints que atuam em comunicação com o Mercado Pago.
    - O primeiro envia para o método que gera o link de pagamento do Mercado Pago.
    - O segundo é um webhook que fica aguardando a confirmação de pagamento do Mercado Pago.
"""

from flask import Blueprint, request, jsonify
from services.mercado_pago import gerar_link, confirma_pagamento
from config import memory

routes_mp_bp = Blueprint('routes_mp_bp', __name__)

@routes_mp_bp.route('/gera_link_mp', methods=['POST'])
def criar_venda():
    """
    Esse endpoint é responsável por receber as informações do BotConversa por método POST e 
    mantém o telefone da pessoa em memória para poder confirmar o pagamento em seguida. Logo 
    após, envia para o método :func:`services.mercado_pago.gerar_link`, passando os dados do usuário.
    """
    
    data = request.get_json()
    print(data)
    '''
    Aqui vou precisar passar o código para gerar o link correto pro método gerar_link
    '''
    # Aqui os dados do cliente são enviados para o método gerar_link()
    link_mp = { 'link_mp' : gerar_link(data)}
    print('memory no flask')
    print(memory)
    #print(link_mp)
    # Aqui retornamos ao BotConversa com o link de pagamento do Mercado Pago
    return jsonify(link_mp)

@routes_mp_bp.route('/webhook_mp', methods=['POST'])
def webhook_mp():
    """
    Esse endpoint fica aguardando o retorno do mercado pago em relação ao pagamento. Ele recebe um POST com os dados
    do cliente, como aprovação ou não do pagamento e telefone, os quais utilizamos em :func:`services.mercado_pago.confirma_pagamento` para
    confrontar os dados e confirmar o pagamento do cliente.
    """
    data = request.get_json()
    #print(data)
    response = confirma_pagamento(data)
    return ''
