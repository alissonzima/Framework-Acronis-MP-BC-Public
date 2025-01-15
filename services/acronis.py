"""
Esse é o coração da comunicação com a Acronis. Toda a automatização é feita aqui.

 Autor: 
  Álisson Zimermann
 Data: 
  30/03/2023
 
 Explicação: 
  Esse arquivo conta com onze métodos efetuando as mais diversas tarefas, especialmente em comunicações com a API da Acronis.
    - O primeiro método serve para renovar o token de autorização com a Acronis.
    - O segundo método é chamado antes de qualquer requisição à Acronis, para verificar se o token de autorização ainda é válido.
    - O terceiro método serve para armazenar uma variável com o meu ID Acronis.
    - O quarto método serve para checar na Acronis se o login solicitado pelo cliente está disponível e é válido.
    - O quinto método faz a criação do 'tenant' (cliente) dentro da plataforma da Acronis.
    - O sexto método faz a criação do usuário do cliente.
    - O sétido método seta o plano de cobrança solicitado pelo cliente.
    - O oitavo método ajusta o papel (role) do cliente, removendo ele da lista de admins.
    - O nono método serve para solicitar à API Acronis o envio do email de confirmação de compra e criação de senha ao cliente.
    - O décimo método faz a cópia do plano de segurança adquirido pelo cliente, do nosso cliente base (Seven) para o cliente recém criado.
    - O último método serviria para setar a quota do pacote do cliente. Atualmente está em desuso.
"""

from base64 import b64encode  # Used for encoding to Base64
import requests
import json
from prices.licencas import licencas
from prices.notary import notarys

client_id = 'put_client_id'
client_secret = 'put_client_secret'
datacenter_url = 'https://us-cloud.acronis.com'
base_url = '{}/api/2'.format(datacenter_url)
auth = ""
headers = ""

def get_auth_token():
    """
    Esse método é chamado por :func:`services.acronis.check_auth` sempre que for detectado que o token de 
    autorização com a API Acronis está expirado. Serve para armazenar na memória um novo token válido.

    Retorno
    -------
    auth (dict) : 
        Um dicionário com o bearer token.
    headers (dict) :
        O dicionário contendo os headers para autenticação.
    """
    global client_id, client_secret, datacenter_url, base_url, headers, auth

    encoded_client_creds = b64encode('{}:{}'.format(client_id,client_secret).encode('ascii'))
    basic_auth = {
        'Authorization': 'Basic ' + encoded_client_creds.decode('ascii')
        }

    response = requests.post(
        '{}/idp/token'.format(base_url),
        headers={'Content-Type': 'application/x-www-form-urlencoded', **basic_auth},
        data={'grant_type': 'client_credentials'},
        )

    token_info = response.json()
    auth = {'Authorization': 'Bearer ' + token_info['access_token']}
    headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-cache', **auth}
    return auth, headers

def check_auth():
    """
    Esse método é chamado antes de cada requisição para a API da Acronis. Por necessitar de autenticação,
    aqui é tentado fazer um GET teste para pegar os dados do nosso usuário e, caso seja detectado que
    o token já está expirado (erro 401), chama a função :func:`services.acronis.get_auth_token` para 
    efetuar a renovação.
    """    
    global auth, headers
    url_test = 'https://us-cloud.acronis.com/api/2/tenants/put_tenant_id_test'
    response = requests.get(url_test, headers=headers)
    if response.status_code == 401:
        auth, headers = get_auth_token()
    return headers

def pegar_meu_id() :
    """
    Esse método é chamado toda vez que é necessário trazer para memória o UUIID do nosso usuário.
    
    Retorno
    -------
    my_id (str) : 
        UUID do nosso usuário da API
    """
    check_auth()
    response = requests.get('{}/clients/{}'.format(base_url,client_id), headers=auth)
    my_id = response.json()['tenant_id']
    return my_id

def check_login(login) :
    """
    Método usado para verificar na Acronis se o login solicitado pelo cliente, em comunicação
    com o BotConversa, através do endpoint :func:`routes.routes_bc.webhook_bc`.

    Parâmetros
    ----------
    login (str) : 
        Login do cliente.
        
    Retorno
    -------
    status_code (int) : 
        O status da requisição para verificação do login. O retorno correto deve ser 204.
    """
    
    params = {"username": login}
    check_auth()
    response = requests.get('{}/users/check_login'.format(base_url), headers=auth, params=params)
    print('status_code_login_liberado')
    print(response.text) #204 é login liberado
    return response.status_code

def cria_cliente(dados_usuario) :
    """
    Método usado para criar um tenant (cliente-customer) dentro da Acronis.
    Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano` e o atualiza com o UUID do cliente criado.

    Parâmetros
    ----------
    dados_usuario (dict) : 
        Dicionário de dados que percorre todos os métodos, atualizando os valores em cada momento.
            - 'email' (str): email do cliente.
            - 'login' (str): login solicitado pelo cliente.
            - 'cobranca' (str): o modo de cobrança escolhido pelo cliente. Pode ser 'Workload' ou 'Volume'.
            - 'telefone' (str): telefone do clientem, chave primária para busca no BotConversa.
            - 'sobrenome' (str): sobrenome do cliente.
            - 'qtd_espaco' (int): caso a cobrança escolhida pelo cliente tenha sido por 'Volume', contém a quantidade de espaço escolhida.
            - 'item_compra' (str): o item escolhido pelo cliente para compra. É descritivo e utilizado em vários momentos no processo.
            - 'qtd_licencas' (int): caso a cobrança escolhida tenha sido por 'Workload', contém quantas licenças foram solicitadas.
            - 'nome_completo' (str): nome completo do cliente.
            - 'primeiro_nome' (str): primeiro nome do cliente.
        
    Retorno
    -------
    dados_usuario (dict) : 
        - 'tenant_id' (str): insere no dicionário do usuário o código UUID dele assim que criado.
    """

    my_id = pegar_meu_id()

    #Aqui é a criação do cliente, chamado Tenant. Ainda não é o usuário que irá mexer
    tenant = {
        'name': dados_usuario['nome_completo'], #verificar os dados que vem
        'kind': 'customer',
        'parent_id': my_id,
        'internal_tag': 'web',
        'language': 'pt-BR',
        'contact': {
            'email': dados_usuario['email'],
            'phone': dados_usuario['telefone'],
            },
        }
    tenant = json.dumps(tenant, indent=4)
    #print('auth antiga')
    #print(auth)
    check_auth()
    #print('auth nova')
    #print(auth)
    
    response = requests.post(
        '{}/tenants'.format(base_url),
        headers={'Content-Type': 'application/json', **auth},
        data=tenant,
        )
    #print(response.text)
    tenant_id = response.json()['id']
    
    dados_usuario['tenant_id'] = tenant_id
    
    return dados_usuario
    
def cria_usuario(dados_usuario) :
    """
    Método usado para criar o usuário do cliente dentro da Acronis.
    Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano` e o atualiza com o ID do usuário do cliente.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.cria_cliente`
        
    Retorno
    -------
    dados_usuario (dict) : 
        - 'id' (str): insere no dicionário do usuário o ID do usuário recem criado.
    """
    
    #Aqui vem a criação do usuário
    
    user_data = {
        "tenant_id": dados_usuario['tenant_id'],
        "login": dados_usuario['login'],
        "contact": {
            "email": dados_usuario['email'],
            "firstname": dados_usuario['primeiro_nome'],
            "lastname": dados_usuario['sobrenome'],
            "phone": dados_usuario['telefone'],
            "types": ["billing", "management", "technical"] # verificar
        },
        'language': 'pt-BR',
        "notifications": [
            "quota",
            "reports",
            "backup_error",
            "backup_warning",
            "backup_info",
            "backup_daily_report"
        ]
    }
    user_data = json.dumps(user_data, indent=4)
    check_auth()
    response = requests.post(
            '{}/users'.format(base_url),
            headers={'Content-Type': 'application/json', **auth},
            data=user_data,
            )
    user_id = response.json()['id']
    dados_usuario['id'] = user_id
    #version = response.json()['version']
    #personal_tenant_id = response.json()['personal_tenant_id']
    #print('status_code_usuario')
    #print(response.status_code) #200, usuário criado
    
    return dados_usuario
   
def setar_plano(dados_usuario) :
    """
    Método usado para setar o plano de cobrança escolhido pelo usuário.
    Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano` e o atualiza com os itens da Acronis
    que correspondem ao modo de cobrança selecionado.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.cria_usuario`
        
    Retorno
    -------
    dados_usuario (dict) : 
        - 'offering_items' (dict): adiciona um dicionário com todas as features do plano de cobrança escolhido.
    """
    
    plano = dados_usuario.get('plano', None)
    plano_seg = dados_usuario.get('plano_seg', None)
    
    if plano:
        for licenca in licencas:
            if licenca['nome'] == dados_usuario['plano']:
                qtd_pc = int(licenca['qtd_pc'])
                qtd_mobile = int(licenca['qtd_mobile'])
                qtd_server = int(licenca['qtd_server'])
    elif plano_seg:
        for licenca in licencas:
            if licenca['nome'] == dados_usuario['plano_seg']:
                qtd_pc = int(licenca['qtd_pc'])
                qtd_mobile = int(licenca['qtd_mobile'])
                qtd_server = int(licenca['qtd_server'])
    else:
        qtd_pc = 1
        qtd_mobile = 0
        qtd_server = 1
    
    offering_items = []
    
    if 'File' in dados_usuario['item_compra'].capitalize() :
        if dados_usuario['cobranca'].capitalize() == 'Volume' :
            edition = 'fss_per_gigabyte'
            volume = int(dados_usuario['qtd_espaco'])
        else :
            quota = int(dados_usuario['qtd_licencas'])
            volume = dados_usuario['qtd_espaco']
            edition = 'fss_per_user'
        application_id = 'dfd85a5f-a464-32ab-81fd-99bcc66a070f' #APPLICATION DO file SYNC AND SHARE
    elif 'Backup' in dados_usuario['item_compra'] or 'Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra']: 
        if dados_usuario['cobranca'].capitalize() == 'Volume' :
            edition = 'pck_per_gigabyte' #define cobrança por gb
        else :
            edition = 'pck_per_workload'   
        quota = 0 if dados_usuario['qtd_espaco'] == '' else int(dados_usuario['qtd_espaco']) 
        qtd_licencas =  dados_usuario.get('qtd_licencas', 0)
        prefix = 'pg' if edition == 'pck_per_gigabyte' else 'pw'
        application_id = '6e6d758d-8e74-3ae3-ac84-50eb0dff12eb' #APPLICATION DO BACKUP
    else :
        application_id = 'f9c5744e-bd1a-36b6-b0f0-ecd7483e1796' #APPLICATION DO NOTARY
        edition = '*'
        volume = dados_usuario['qtd_espaco']
        for notary in notarys:
            if notary['nome'] == dados_usuario['notary']:
                qtd_autenticacao = int(notary['qtd_autenticacao'])
                qtd_assinatura = int(notary['qtd_assinatura'])
                qtd_template = int(notary['qtd_template'])
        
    check_auth()
    response = requests.get(
        '{}/tenants/{}/offering_items/available_for_child?edition={}&application_id={}'.format(base_url,
                                                                                                pegar_meu_id(),
                                                                                                edition,
                                                                                                application_id),
        headers=headers
        )
    #print(response.text)
    #dr é disaster recovery

    itens = json.loads(response.text)['items']    
    
    for item in itens:
        #print(item)
        infra_id = item.get('infra_id')
        if 'Backup' in dados_usuario['item_compra'] or 'Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra'] :
            if 'Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra']:
                if item['usage_name'] == 'pack_adv_security':
                    item['quota']['value'] = int(qtd_licencas)
                    item['quota']['overage'] = 0 #int(quota * 0.1)
                    item['status'] = 1
                    offering_items.append(item)
                if item['usage_name'] == 'pack_adv_management' and 'Proteção' in dados_usuario['item_compra']:
                    item['quota']['value'] = int(qtd_licencas)
                    item['quota']['overage'] = 0 #int(quota * 0.1)
                    item['status'] = 1
                    offering_items.append(item)
            if f'{prefix}_base_storage' == item['name'] and 'storage' == item['usage_name'] and infra_id == 'c877495b-7910-4e59-b69d-f835d1e0f762':
                item['quota']['value'] = int(quota * 1024 * 1024 * 1024)
                item['quota']['overage'] = int(quota / 10 * 1024 * 1024 * 1024)
                item['status'] = 1
                offering_items.append(item)
            elif f'{prefix}_base' in item['name'] and 'adv' not in item['name'] and 'dr_' not in item['name'] and 'storage' not in item['name']:
                ### É aqui
                    if prefix == 'pw' :
                        if 'workstations' in item['name']:
                            item['quota']['value'] = qtd_pc
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                        elif 'mobiles' in item['name']:
                            item['quota']['value'] = qtd_mobile
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                        elif 'servers' in item['name'] and qtd_server > 0 and 'web' not in item['name'] :
                            item['quota']['value'] = qtd_server
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                    elif prefix == 'pg' and ('Antivírus' in dados_usuario['item_compra'] or 'Proteção' in dados_usuario['item_compra']) :
                        if 'workstations' in item['name']:
                            item['quota']['value'] = qtd_pc
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                        elif 'mobiles' in item['name']:
                            item['quota']['value'] = qtd_mobile
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                        elif 'servers' in item['name'] and qtd_server > 0 and 'web' not in item['name'] :
                            item['quota']['value'] = qtd_server
                            item['quota']['overage'] = 0
                            item['status'] = 1
                            offering_items.append(item)
                    else :               
                        item['status'] = 1
                        offering_items.append(item)
            #elif dados_usuario['item_compra'] == 'Backup de Alta Disponibilidade' and f'{prefix}_base_adv' in item['name']:
            #    item['status'] = 1
            #    offering_items.append(item)
            elif 'Backup de Alta Disponibilidade' in dados_usuario['item_compra'] and f'{prefix}_pack_adv_backup_workstations' == item['name']:
                item['quota']['value'] = 1
                item['quota']['overage'] = 0
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup de Alta Disponibilidade' in dados_usuario['item_compra'] and f'{prefix}_pack_adv_backup_servers' == item['name'] and int(qtd_server) > 0:
                item['quota']['value'] = 1
                item['quota']['overage'] = 0
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup' in dados_usuario['item_compra'] and f'{prefix}_base_dr' in item['name'] and infra_id == '3ba2f03b-fdfb-401a-b1b0-38f5ced5655a':
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup' in dados_usuario['item_compra'] and f'{prefix}_base_adv_dr_storage' in item['name'] and infra_id == '3ba2f03b-fdfb-401a-b1b0-38f5ced5655a':
                item['quota']['value'] = int(quota * 1024 * 1024 * 1024)
                item['quota']['overage'] = int(quota / 10 * 1024 * 1024 * 1024)
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup' in dados_usuario['item_compra'] and f'{prefix}_base_adv_dr_compute_points' in item['name'] and infra_id == '3ba2f03b-fdfb-401a-b1b0-38f5ced5655a':
                item['quota']['value'] = 115200
                item['quota']['overage'] = 10800
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup' in dados_usuario['item_compra'] and f'{prefix}_base_adv_dr_cloud_servers' in item['name'] and infra_id == '3ba2f03b-fdfb-401a-b1b0-38f5ced5655a':
                item['quota']['value'] = 1
                item['quota']['overage'] = 0
                item['status'] = 1
                offering_items.append(item)
            elif 'Backup' in dados_usuario['item_compra'] and f'{prefix}_base_adv_dr_internet_access' in item['name'] and infra_id == '3ba2f03b-fdfb-401a-b1b0-38f5ced5655a':
                item['status'] = 1
                offering_items.append(item)                
                
                
        else :
            if 'Notary' in dados_usuario['item_compra'].capitalize() and application_id in item['application_id'] :
                if 'storage' in item['name'] :
                    item['quota']['value'] = int(volume) * 1024 * 1024
                    item['quota']['overage'] = 0
                    item['status'] = 1
                    offering_items.append(item)
                elif 'notarizations' in item['name'] :
                    item['quota']['value'] = int(qtd_autenticacao)
                    item['quota']['overage'] = 0
                    item['status'] = 1
                    offering_items.append(item)   
                elif 'esignatures' in item['name'] :         
                    item['quota']['value'] = int(qtd_assinatura)
                    item['quota']['overage'] = 0
                    item['status'] = 1
                    offering_items.append(item)
                elif 'document_templates' in item['name'] :         
                    item['quota']['value'] = int(qtd_template)
                    item['quota']['overage'] = 0
                    item['status'] = 1
                    offering_items.append(item)            
                        
            else :
                if application_id in item['application_id'] and 'child' not in item['name'] and 'adv' not in item['name']:
                    if infra_id == 'fde507e9-275b-414d-a0e4-3440f33bc881' :
                        #print(volume)
                        item['quota']['value'] = int(volume) * 1024 * 1024 * 1024
                        item['quota']['overage'] = 0
                    if 'fc_seats' in item['usage_name'] :
                        item['quota']['value'] = None if edition == 'fss_per_gigabyte' else quota
                        item['quota']['overage'] = None if edition == 'fss_per_gigabyte' else int(quota * 0.1)
                    offering_items.append(item)
        
    payload = {'offering_items': offering_items}
    #print(payload)
    check_auth()
    r = requests.put('{}/tenants/{}/offering_items'.format(base_url, dados_usuario['tenant_id']), 
                        headers={'Content-Type': 'application/json', **auth},
                        json=payload)
    
    #print('habilitando o plano')
    #print(r.text)
    dados_usuario['offering_items'] = json.loads(r.text)['items']
    #print (dados_usuario)
    return dados_usuario
    
def ajustar_roles(dados_usuario) :
    """
    Método usado para definir o papel do usuário (role). Por padrão ele é criado como admin, então aqui
    atualizamos ele para o papel de 'backup_user', permitindo apenas alterar o plano de proteção.
    Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano`.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.setar_plano`
    """
    
    policies_object = {
    "items": [
        {
            "id": "00000000-0000-0000-0000-000000000000",
            "issuer_id": "00000000-0000-0000-0000-000000000000",
            "trustee_id": dados_usuario['id'],
            "trustee_type": "user",
            "tenant_id": dados_usuario['tenant_id'],
            "role_id": "backup_user",
            "version": 0
        }
    ]
    }

    policies_object = json.dumps(policies_object, indent=4)
    check_auth()
    response = requests.put(
        '{}/users/{}/access_policies'.format(base_url, dados_usuario['id']),
        headers={'Content-Type': 'application/json', **auth},
        data=policies_object
    )
    #print('put policies')
    #print(response.text)
    #print(response)
    check_auth()
    response = requests.get('{}/users/{}/access_policies'.format(base_url, dados_usuario['id']), headers={'Content-Type': 'application/json', **auth})
    #print('criação policies')
    #print(response.text)
    
    return dados_usuario


def enviar_email_confirmacao(dados_usuario) :
    """
    Método usado para enviar à Acronis a solicitação para o envio do email de 
    confirmação da compra. Nesse email o usuário irá criar a senha e fazer seu primeiro acesso.
    Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano`.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.ajustar_roles`
        
    Retorno
    -------
    dados_usuario (dict) : o mesmo dicionário recebido.
    """
    
    check_auth()
    requests.post('{}/users/{}/send-activation-email'.format(base_url, dados_usuario['id']), 
                         headers={'Content-Type': 'application/json', **auth})
    #print('codigo_email_conf')
    #print(response.status_code) #204 enviou o email com sucesso
    return dados_usuario 

def copiar_policy(dados_usuario) : 
    """
    Método usado para fazer a cópia do plano de segurança, que está no nosso usuário padrão (Seven), para
    o cliente recém criado. Recebe os dados do usuário de :func:`routes.routes_bc.criar_plano`.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.enviar_email_confirmacao`
    """
    
    check_auth()
    print(dados_usuario['tenant_id'])
    uuid_usuario = dados_usuario['tenant_id']
    response = requests.get(f'{datacenter_url}/api/1/groups/{uuid_usuario}', headers=headers)
    cliente_int_id = json.loads(response.text)['id']
    print(cliente_int_id)
    
    if 'Backup' in dados_usuario['item_compra'] or 'Antivírus' in dados_usuario['item_compra'] or "Familiar" in dados_usuario['item_compra']:

        response = requests.get(f'{datacenter_url}/api/policy_management/v4/policies?tenant_id=3778272&enabled=true', headers=headers)
        #response.text
        planos = json.loads(response.text)

        name = dados_usuario['item_compra']

        for plano in planos['items'] :
            for principal in plano['policy']:
                if principal.get('name', '') == name :
                    id_principal = principal['id']
                    break

        link = f'{datacenter_url}/api/policy_management/v4/policies/{id_principal}?full_composite=true&include_settings=true&include_applied_context=true&enabled=true'
        response = requests.get(link, headers=headers)
        #response.text
        plan_data = {
            'subject': response.json(),
            'override_tenant_id' : str(cliente_int_id),
            'ignore_policy_and_tenant_ids' : True
        }

        url = f"{datacenter_url}/api/policy_management/v4/policies"

        payload = json.dumps(plan_data, ensure_ascii=False).encode('utf-8')

        response = requests.post(url, headers=headers, data=payload)
        #print(response.text)
    
def setar_quota(dados_usuario, i) :
    """
    Método foi pensado para modificar a quota do usuário, mediante aquisição de upgrade. Ainda não
    foi implementado.

    Parâmetros
    ----------
    dados_usuario (dict) : ver :func:`services.acronis.copiar_policy`.
    i (int) : a versão atual da quota. Cada atualização de valores na Acronis precisa passar a versão nova (i+1) para ser armazenado.

    Retorno
    -------
    dados_usuario (dict) : o mesmo dicionário recebido.
    """
    
    print('dados usuario')
    print(dados_usuario)
    value = dados_usuario['quota'] * 1024 * 1024 * 1024 # 10 gb
    overage = (dados_usuario['quota'] + 2) * 1024 * 1024 * 1024
    version = dados_usuario['offering_items'][0]['quota']['version'] + 1
    
    dados_usuario['offering_items'][0]['quota']['overage'] =  overage
    dados_usuario['offering_items'][0]['quota']['value'] = value 
    dados_usuario['offering_items'][0]['quota']['version'] = version
    
    print('dados usuario 2')
    print(dados_usuario)

    updated_offering_items = {
        'offering_items': dados_usuario['offering_items']
        }

    updated_offering_items = json.dumps(updated_offering_items, indent=4)
    check_auth()
    response = requests.put(
        '{}/tenants/{}/offering_items'.format(base_url, dados_usuario['tenant_id']),
        headers={'Content-Type': 'application/json', **auth},
        data=updated_offering_items
        )
    print('cotas')
    print(response.text)
    
    return dados_usuario 
