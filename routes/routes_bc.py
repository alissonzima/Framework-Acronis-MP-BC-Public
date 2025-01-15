"""
Esse é uma blueprint que condensa os endpoints de comunicação na parte do BotConversa.

 Autor: 
  Álisson Zimermann
 Data: 
  29/03/2023
 
 Explicação: 
  Aqui temos atualmente cinco endpoints que atuam em comunicação com o BotConversa.
    - O primeiro checa se o login da acronis é válido, logo após envia um email para validar o @ndereço do cliente.
    - O segundo é um teste de comunicação com o BotConversa que cria um anagrama com o nome do cliente.
    - O terceiro é o coração da interação BotConversa com Acronis, criando o tenant(cliente), o usuário e o plano de proteção do mesmo.
    - O quarto foi inicialmente um teste de manipulação de imagem para envio de mensagens personalizadas ao BotConversa. Hoje está incorporado no fluxo.
    - O quinto é o metodo de validação de email do cliente.
"""
from urllib.parse import unquote
from flask import Blueprint, request, jsonify, render_template
from services.methods import *
from services.acronis import *
from config import user_tokens, email_validado
from prices.licencas import licencas
from prices.planos import planos
from prices.notary import notarys
from services.safeleads import *


routes_bc_bp = Blueprint('routes_bc_bp', __name__)
 

@routes_bc_bp.route('/webhook_bc', methods=['POST'])
def webhook_bc():
    """
    Esse endpoint é responsável por receber as informações do BotConversa por método POST para
    verificação da disponibilidade do login Acronis, no método :func:`services.acronis.check_login` e, caso sim, envia um email ao cliente para valiação
    do mesmo, pela função :func:`services.methods.enviar_email_validacao`.
    """
    data = request.get_json()
    print(data)
    #checagem de login acronis
    status_code = check_login(data['login'])
    print(status_code)
    if status_code == 204 :
        return(jsonify({'status_code_bp' : 200}))
    else :
        return(jsonify({'status_code_bp' : 409}))
    
@routes_bc_bp.route('/nome', methods=['POST'])
def nome():
    """
    Esse endpoint foi um teste de comunicação do servidor com o BotConversa. Ele recebe o nome 
    do cliente e retorna um anagrama, através da função :func:`services.methods.generate_anagram`.
    """
    data = request.get_json()
    print(data)
    name_return = generate_anagram(data['name'])
    return name_return

@routes_bc_bp.route('/criar_plano', methods=['POST'])
def criar_plano():
    """
    Esse endpoint faz toda a comunicação com a Acronis para criação do cliente.
      - Na função :func:`services.acronis.cria_cliente` o cliente será criado, 
      - Na função :func:`services.acronis.cria_usuario` o perfil do usuário do cliente será criado.
      - Na função :func:`services.acronis.setar_plano` será definido as permissões do plano adquirido pelo cliente.
      - Na função :func:`services.acronis.ajustar_roles` será setada as permissões do usuário do cliente.
      - Na função :func:`services.acronis.enviar_email_confirmacao` é solicitado à acronis que envie o email de confirmação ao cliente.
      - Na função :func:`services.acronis.copiar_policy` será copiado para o perfil do cliente o plano de proteção.
    """
    data = request.get_json()
    print(data)
    data = cria_cliente(data)
    data = cria_usuario(data)
    data = setar_plano(data)
    data = ajustar_roles(data)
    data = enviar_email_confirmacao(data)
    data = copiar_policy(data)
    return ''

@routes_bc_bp.route('/envia_imagem', methods=['POST'])
def envia_imagem():
    """
    Esse endpoint inicialmente foi um teste de manipulação de imagem. Hoje se comunica com o BotConversa após
    criar e manipular uma imagem de post it com o nome e telefone do cliente, através da função :func:`services.methods.processa_imagem`.
    """    
    data = request.get_json()   
    data = processa_imagem(data)
    return data

@routes_bc_bp.route('/valida_email', methods=['GET'])
def valida_email():
    """
    Esse endpoint é um webhook que faz a validação do email do cliente. Recebe por método GET os parâmetros
    enviados no email, sendo eles o token único do cliente, o email e o telefone, para enviar ao webhook do
    BotConversa a confirmação de validação, através do método :func:`services.methods.validacao_email`.
    
    Parâmetros
    ----------
        'token' (str) : 
            Token único gerado para o cliente
        'email' (str) : 
            O email do cliente
        'phone' (str) : 
            Telefone do cliente como chave para o BotConversa
    
    Retorno
    -------
        html : str
            Ele retorna para o cliente um html mostrando que o email foi validado com sucesso.
    """    
    token = request.args.get('token')
    email = request.args.get('email')
    nome = unquote(request.args.get('nome'))
    telefone = request.args.get('phone')
    
    if email and token:
        if email not in email_validado:
            if user_tokens.get(email) == token:
                # validação bem sucedida
                validacao_email(telefone, 'sucesso', nome)
                user_tokens.pop(email)
                email_validado[email] = True
                html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'><style>html,body{{height:100%;}}body{background-color:#333d53;display:flex;align-items:center;justify-content:center;}div{background-color:#fff;width:80%;max-width:350px;padding:20px;border-radius:10px;text-align:center;}</style></head><body><div><p>Seu email foi validado com sucesso. Você pode fechar essa janela agora.</p></div></body></html>"
                return html
        else:
            # email já validado
            email_validado.pop(email)
            html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'><style>html,body{{height:100%;}}body{background-color:#333d53;display:flex;align-items:center;justify-content:center;}div{background-color:#fff;width:80%;max-width:350px;padding:20px;border-radius:10px;text-align:center;}</style></head><body><div><p>Seu email já foi validado. Você pode fechar essa janela agora.</p></div></body></html>"
            return html

    # validação falhou
    return ''

@routes_bc_bp.route('/config', methods=['GET'])
def config_lista():
    """
    ###
    Parâmetros
    ----------
        '###' (###) : 
            ###
    
    Retorno
    -------
        ### : ###
            ###
    """    
    return render_template('config.html', planos=planos, licencas=licencas, notarys=notarys)

@routes_bc_bp.route('/config', methods=['POST'])
def config_salva():
    """
    ###
    Parâmetros
    ----------
        '###' (###) : 
            ###
    
    Retorno
    -------
        ### : ###
            ###
    """    
    licencas_temp = {}
    planos_temp = {}
    notarys_temp = {}

    for chave, valor in request.form.items():
        if chave.startswith('plano'):
            # Adiciona a chave e valor ao dicionário de licenças
            licencas_temp[chave] = valor
        elif chave.startswith('notary'):
            # Adiciona a chave e valor ao dicionário de planos
            notarys_temp[chave] = valor
        else :
            # Adiciona a chave e valor ao dicionário de notary
            planos_temp[chave] = valor
            
    result = {}
    for key, value in licencas_temp.items():
        prefix = key.split('_')[0] + '_' + key.split('_')[1]
        if prefix not in result:
            result[prefix] = {}
        result[prefix][key] = value
        
    for key in result.keys():
        result[key] = {k: v for k, v in result[key].items() if v != ""}
        
    #print(result)
    licencas = []
    for key in result.keys():
        licenca = {}
        for k, v in result[key].items():
            new_key = k.replace(key + '_', '')
            licenca[new_key] = v
        licencas.append(licenca)
        
    resultp = {}
    for key, value in planos_temp.items():
        prefix = key.split('_')[0] + '_' + key.split('_')[1] + '_' + key.split('_')[2]
        if prefix not in resultp:
            resultp[prefix] = {}
        resultp[prefix][key] = value
        
    for key in resultp.keys():
        resultp[key] = {k: v for k, v in resultp[key].items() if v != ""}
        
    planos = []
    for key in resultp.keys():
        plano = {}
        for k, v in resultp[key].items():
            new_key = k.replace(key + '_', '')
            plano[new_key] = v
        planos.append(plano)
        
    result = {}
    for key, value in notarys_temp.items():
        prefix = key.split('_')[0] + '_' + key.split('_')[1]
        if prefix not in result:
            result[prefix] = {}
        result[prefix][key] = value
        
    for key in result.keys():
        result[key] = {k: v for k, v in result[key].items() if v != ""}
        
    #print(result)
    notarys = []
    for key in result.keys():
        notary = {}
        for k, v in result[key].items():
            new_key = k.replace(key + '_', '')
            notary[new_key] = v
        notarys.append(notary)
        
    resultp = {}
    for key, value in notarys_temp.items():
        prefix = key.split('_')[0] + '_' + key.split('_')[1] + '_' + key.split('_')[2]
        if prefix not in resultp:
            resultp[prefix] = {}
        resultp[prefix][key] = value
        
    for key in resultp.keys():
        resultp[key] = {k: v for k, v in resultp[key].items() if v != ""}
    
    # Obter o caminho absoluto do arquivo main.py
    main_path = os.path.abspath(__file__)   
    
    # Obter o diretório que contém o arquivo main.py
    main_dir = os.path.dirname(main_path)
    
    # Construir o caminho absoluto do arquivo licencas.py
    licencas_path = os.path.join(main_dir, '..', 'prices', 'licencas.py')
    
    # Construir o caminho absoluto do arquivo planos.py
    planos_path = os.path.join(main_dir, '..', 'prices', 'planos.py')
    
    # Construir o caminho absoluto do arquivo notarys.py
    notarys_path = os.path.join(main_dir, '..', 'prices', 'notary.py')
    
    with open(licencas_path, 'w', encoding='utf-8') as f:
        f.write('licencas = ')
        json.dump(licencas, f, ensure_ascii=False, indent=4)
            
    with open(planos_path, 'w', encoding='utf-8') as f:
        f.write('planos = ')
        json.dump(planos, f, ensure_ascii=False, indent=4)
        
    with open(notarys_path, 'w', encoding='utf-8') as f:
        f.write('notarys = ')
        json.dump(notarys, f, ensure_ascii=False, indent=4)
    
    return '<button onclick="window.history.back()">Voltar</button>'

@routes_bc_bp.route('/retorna_preco', methods=['POST'])
def retorna_preco():
    """
    ###
    Parâmetros
    ----------
        '###' (###) : 
            ###
    
    Retorno
    -------
        ### : ###
            ###
    """
    data = request.get_json()
    print(data)
    
    if data['plano']:
        for item in licencas:
            if item['nome'] == data['plano']:
                qtd_licencas = int(item['qtd_pc']) + int(item['qtd_mobile']) + int(item['qtd_server'])
                
        for item in planos:
            if item['nome'] == data['item_compra'] + ' ' + data['plano'][-1]:
                if item['cobranca'] == data['cobranca'] :
                    if item['volume'] == data['qtd_espaco']  :
                        valor_plano = item['valor']
                        print(valor_plano, ' ', qtd_licencas)
                        return jsonify({'qtd_licencas' : qtd_licencas, 'valor_plano' : valor_plano})

    elif 'Antivírus' in data['item_compra'] or 'Proteção' in data['item_compra'] :
        for item in planos:
            if data['item_compra'] == item['nome'] :
                valor = item['valor'].replace(',', '.')
                valor_plano = float(data['qtd_licencas']) * float(valor)
                print(valor_plano)
                return jsonify({'valor_plano' : valor_plano})
    
    elif 'Notary' in data['item_compra']:
        for item in planos:
            if item['nome'] == data['item_compra']:
                if item['cobranca'] == data['cobranca'] :
                    if item['volume'] == data['qtd_espaco'] :
                        valor_plano = item['valor']
                        print(valor_plano)
                        return jsonify({'valor_plano' : valor_plano})
        
    else :
        for item in planos:
            if item['nome'] == data['item_compra'] :
                if item['cobranca'] == data['cobranca'] :
                    if item['volume'] == data['qtd_espaco']  :
                        valor_plano = item['valor']
                        print(valor_plano)
                        return jsonify({'valor_plano' : valor_plano})
    
@routes_bc_bp.route('/confirmar_email', methods=['POST'])
def confirmar_email():
    """

    """
    data = request.get_json()
    enviar_email_validacao(data)
    return ''

@routes_bc_bp.route('/gera_proposta', methods=['POST'])
def gera_proposta():
    """

    """
    dados_usuario = request.get_json()
    inicio(dados_usuario)
    return ''

@routes_bc_bp.route('/upload_imagens', methods=['GET'])
def upload_imagens():
    """ 

    """
    id_projeto = request.args.get('id_projeto')
    return render_template('upload_imagens.html', id_projeto=id_projeto)

@routes_bc_bp.route('/salva_imagens', methods=['POST'])
def salva_imagens():
    """
    
    """
    data = request.files
    id_projeto = request.form['id_projeto']
    saida = upload_arquivos(data, 1, id_projeto)
    
    return saida


@routes_bc_bp.route('/upload_pdf', methods=['GET'])
def upload_pdf():
    """ 

    """
    id_projeto = request.args.get('id_projeto')
    return render_template('upload_pdf.html', id_projeto=id_projeto)

@routes_bc_bp.route('/salva_pdf', methods=['POST'])
def salva_pdf():
    """
    
    """
    data = request.files
    id_projeto = request.form['id_projeto']
    saida = upload_arquivos(data, 2, id_projeto)
    
    return saida

@routes_bc_bp.route('/upload_fotos', methods=['GET'])
def upload_fotos():
    """ 

    """
    id_tarefa = request.args.get('id_tarefa')
    return render_template('upload_fotos.html', id_tarefa=id_tarefa)

@routes_bc_bp.route('/salva_fotos', methods=['POST'])
def salva_fotos():
    """
    
    """
    data = request.files
    
    id_tarefa = request.form['id_tarefa']

    dados = {
        'id_projeto' : put_id_projeto,
        'id_tarefa' : id_tarefa
    }
    saida = upload_arquivos(data, 3, dados)
    
    return saida

@routes_bc_bp.route('/cria_tarefa', methods=['POST'])
def cria_tarefa():
    """
    
    """
    data = request.get_json()
    
    id_tarefa = insere_tarefa(data)
    
    return id_tarefa
