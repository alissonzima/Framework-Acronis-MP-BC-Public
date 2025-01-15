"""
Esse é um Framework que atua trocando informações com o BotConversa, Acronis API e Mercado Pago API.

 Autor: 
  Álisson Zimermann
 Data: 
  28/03/2023
 
 Explicação: 
  Este arquivo mantém o webservice rodando e redireciona as rotas tanto do BotConversa
  quanto do Mercado Pago aos seus respectivos endpoints. Blueprints são esses conjuntos de endpoints.
  Esse é um arquivo padrão e não necessita ser modificado. O aplicativo sempre deve ser rodado por esse arquivo.
"""

from flask import Flask
from routes.routes_bc import routes_bc_bp
from routes.routes_mp import routes_mp_bp
import os

# Cria uma instância do flask
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
# Configuração para servir arquivos estáticos
app.static_folder = 'docs/_static'
# Registra o conjunto de blueprints de rotas do BotConversa
app.register_blueprint(routes_bc_bp)
# Registra o conjunto de blueprints de rotas do Mercado Pago
app.register_blueprint(routes_mp_bp)

# Inicia o servidor Flask, à partir desse arquivo
if __name__ == '__main__':
    app.run(debug=True)
