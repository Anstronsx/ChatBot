#Instalamos flask en nuestro entorno venv 
from flask import Flask, request, jsonify, render_template 
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask (__name__)

#Configuración de la base de datos sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#Instanciamos la clase SQLAlchemy
db = SQLAlchemy(app)

#Definimos la clase modelo
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto =db.Column(db.TEXT)


#Crear una tabla si no existe
with app.app_context():
    db.create_all()

#Funcion para ordenar los registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora or datetime.min, reverse=True)


@app.route('/')
def index():

    #Obtener todos los registros de la base de datos
    registros = Log.query.all()
    #Ordenar los registros por fecha y hora
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html',registros=registros_ordenados)

mensajes_log = []

#Funcion para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)

    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

#"Token de verificación para la configuracion"
TOKEN_OMICTECH = "OMICTECH"

#Creacion del wbhook

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    #Importar metodo de META
    if request.method== 'GET':
        challenge  = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes (request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_OMICTECH:
        return challenge
    else:
        return jsonify({'ERROR': 'TOKEN INVALIDO'}), 401
    

def recibir_mensajes(req):
    req = request.get_json()

    agregar_mensajes_log(req)
    return jsonify({'message': 'EVENT_RECEIVED'})



if __name__== '__main__':
    app.run(host='0.0.0.0',port=80, debug=True)